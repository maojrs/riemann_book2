"""Check built pages for horizontal scroll bars, in headless Firefox.

For each page and window width it waits until the outputs have rendered, then reports
  - page_hscroll: whether the whole page scrolls sideways,
  - every element inside the article that shows a horizontal scroll bar,
  - every element that sticks out past the right edge of the window,
and saves a full-page screenshot.

Needs Firefox and the Marionette client, kept out of the book's environment:
    uv venv /tmp/pagecheck-env && VIRTUAL_ENV=/tmp/pagecheck-env uv pip install marionette_driver
Serve the built site, then run (PAGE is the URL path, "." for the root page):
    (cd _build/html && python3 -m http.server 8767 --bind 127.0.0.1) &
    /tmp/pagecheck-env/bin/python -W ignore .agents/tools/pagecheck.py http://127.0.0.1:8767 /tmp/shots 390,768,1280,1440,1920 acoustics
Run it from a directory that has no file named like a standard module (e.g. /tmp).
With --live, every interactive figure is made live first (Python runs in the page; slow).
"""
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

from marionette_driver.marionette import Marionette

live = '--live' in sys.argv          # first make every interactive figure live (Python in the page)
args = [a for a in sys.argv[1:] if a != '--live']
base, outdir, widths, pages = args[0], args[1], [int(w) for w in args[2].split(',')], args[3:]
os.makedirs(outdir, exist_ok=True)
profile = tempfile.mkdtemp(prefix='ffprof')
port = 2829
proc = subprocess.Popen(['firefox', '--headless', '--no-remote', '--profile', profile, '--marionette',
                         '--remote-allow-system-access'],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        env={**os.environ, 'MOZ_MARIONETTE_PORT': str(port)})
with open(os.path.join(profile, 'user.js'), 'a') as f:
    f.write(f'user_pref("marionette.port", {port});\n')
time.sleep(4)
client = Marionette(host='127.0.0.1', port=port)
client.start_session()

OVERFLOW_JS = r"""
const out = {page: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
             pageScrollWidth: document.documentElement.scrollWidth,
             clientWidth: document.documentElement.clientWidth, scrollers: [], loading: 0};
out.loading = [...document.querySelectorAll('article *')].filter(e => e.childElementCount === 0 && e.textContent.trim() === 'Loading...').length;
for (const e of document.querySelectorAll('article *')) {
  const cs = getComputedStyle(e);
  if (cs.display === 'none' || e.clientWidth === 0) continue;
  const scrolls = (cs.overflowX === 'auto' || cs.overflowX === 'scroll') && e.scrollWidth > e.clientWidth + 1;
  if (scrolls) {
    const label = (e.tagName + '.' + [...e.classList].slice(0, 3).join('.')).slice(0, 80);
    const text = (e.innerText || '').trim().slice(0, 70).replace(/\s+/g, ' ');
    out.scrollers.push({el: label, scrollWidth: e.scrollWidth, width: e.clientWidth, text});
  }
}
out.wide = [];
const vw = document.documentElement.clientWidth;
for (const e of document.querySelectorAll('body *')) {
  const r = e.getBoundingClientRect();
  if (r.width > 0 && r.right > vw + 1 && getComputedStyle(e).position !== 'fixed') {
    let p = e.parentElement, clipped = false;
    while (p) { const o = getComputedStyle(p).overflowX; if (o !== 'visible') { clipped = true; break; } p = p.parentElement; }
    if (!clipped) out.wide.push({el: (e.tagName + '.' + [...e.classList].slice(0, 3).join('.')).slice(0, 70), right: Math.round(r.right), text: (e.innerText || '').trim().slice(0, 50).replace(/\s+/g, ' ')});
  }
}
out.wide = out.wide.slice(0, 8);
return out;
"""

in_frame = []        # non-empty while the checks run inside the emulation frame


def open_page(url, width):
    """Open url `width` CSS pixels wide. Firefox windows cannot be narrower than 500 px, so
    narrower screens are emulated with a frame of that width (as responsive-design tools
    do); the checks and the screenshot then run inside the frame."""
    if in_frame:
        client.switch_to_frame()                    # back to the top page
        in_frame.clear()
    if width >= 500:
        client.set_window_rect(width=width, height=1000)
        client.navigate(url)
        return None
    client.set_window_rect(width=600, height=1000)
    client.navigate(base + '/__no_such_page__')     # a plain page of the same origin
    client.execute_script(f"""document.open();
        document.write('<body style="margin:0"><iframe id="frame" src="{url}" style="border:0;width:{width}px;height:1000px"></iframe></body>');
        document.close();""")
    frame = client.find_element('id', 'frame')
    time.sleep(2)
    client.switch_to_frame(frame)
    in_frame.append(True)
    # phones overlay their scroll bars, so they take no width
    client.execute_script("document.documentElement.style.scrollbarWidth = 'none'")
    return frame


def screenshot(frame):
    """Full-page screenshot (of the frame's whole page when emulating a narrow screen)."""
    if frame is None:
        return client.screenshot(full=True)
    height = client.execute_script('return document.documentElement.scrollHeight')
    client.switch_to_frame()
    in_frame.clear()
    client.execute_script(f"document.getElementById('frame').style.height = '{height}px'")
    client.set_window_rect(width=600, height=min(height + 50, 30000))
    return client.screenshot(element=frame)


LIVE_JS = r"""
const done = arguments[0];
const roots = [...document.querySelectorAll('*')].filter(e => e.shadowRoot).map(e => e.shadowRoot.querySelector('[class]')).filter(Boolean);
(async () => {
  for (const el of roots) {
    el.scrollIntoView({block: 'center'});
    const t0 = performance.now();
    while (!el.dataset.state && performance.now() - t0 < 240000) await new Promise(r => setTimeout(r, 200));
  }
  window.scrollTo(0, 0);
  done(roots.map(el => el.dataset.state || 'timeout'));
})();
"""


report = {}
client.timeout.script = 3600
try:
    for page in pages:
        for w in widths:
            frame = open_page(f'{base}/{page}/', w)
            for _ in range(40):                     # wait until outputs are rendered
                time.sleep(0.5)
                if client.execute_script(OVERFLOW_JS)['loading'] == 0:
                    break
            time.sleep(1.0)
            if live:
                states = client.execute_async_script(LIVE_JS)
                if any(state != 'ready' for state in states):
                    print(f'    interactive figures not live: {states}')
            res = client.execute_script(OVERFLOW_JS)
            report[f'{page}@{w}'] = res
            png = screenshot(frame)
            with open(os.path.join(outdir, f'{page}_{w}.png'), 'wb') as f:
                f.write(base64.b64decode(png))
            if frame is not None:
                assert res['clientWidth'] == w, res['clientWidth']   # emulated phone width
            print(f"{page}@{w}: page_hscroll={res['page']} still_loading={res['loading']} scrollers={len(res['scrollers'])}")
            for x in res['wide']:
                print(f"    WIDER THAN WINDOW: {x['el']:40s} right={x['right']} {x['text']!r}")
            for s in res['scrollers']:
                print(f"    {s['el']:45s} {s['scrollWidth']:5d} > {s['width']:5d}  {s['text']!r}")
finally:
    json.dump(report, open(os.path.join(outdir, 'report.json'), 'w'), indent=1)
    client.delete_session()
    proc.terminate()
    proc.wait()
    shutil.rmtree(profile, ignore_errors=True)       # each run uses a fresh profile
