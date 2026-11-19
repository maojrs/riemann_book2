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
"""
import base64
import json
import os
import subprocess
import sys
import tempfile
import time

from marionette_driver.marionette import Marionette

base, outdir, widths, pages = sys.argv[1], sys.argv[2], [int(w) for w in sys.argv[3].split(',')], sys.argv[4:]
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

report = {}
for page in pages:
    for w in widths:
        client.set_window_rect(width=w, height=1000)
        client.navigate(f'{base}/{page}/')
        for _ in range(40):                     # wait until outputs are rendered
            time.sleep(0.5)
            if client.execute_script(OVERFLOW_JS)['loading'] == 0:
                break
        time.sleep(1.0)
        res = client.execute_script(OVERFLOW_JS)
        report[f'{page}@{w}'] = res
        png = client.screenshot(full=True)
        with open(os.path.join(outdir, f'{page}_{w}.png'), 'wb') as f:
            f.write(base64.b64decode(png))
        print(f"{page}@{w}: page_hscroll={res['page']} still_loading={res['loading']} scrollers={len(res['scrollers'])}")
        for x in res['wide']:
            print(f"    WIDER THAN WINDOW: {x['el']:40s} right={x['right']} {x['text']!r}")
        for s in res['scrollers']:
            print(f"    {s['el']:45s} {s['scrollWidth']:5d} > {s['width']:5d}  {s['text']!r}")
json.dump(report, open(os.path.join(outdir, 'report.json'), 'w'), indent=1)
client.delete_session()
proc.terminate()
