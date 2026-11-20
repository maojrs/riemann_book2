// Shallow water phase-plane explorer: drag q_l and q_r in the h-hu plane, and the time in the
// x-t plane. Shown: the curves of states connected to q_l by a 1-wave and to q_r by a 2-wave
// (shocks red, rarefactions blue; dashed where unphysical), the middle state, the waves in the
// x-t plane, and the depth and momentum at time t. The Riemann solution is computed by the
// book's exact solver (exact_solvers/shallow_water.py, through widgets/compute.py) running in
// the browser; D3 draws it. MyST markup:
//
//   ```{anywidget} ../widgets/shallow_water_explorer.mjs
//   :css: ../widgets/acoustics_explorer.css
//   {"ql": [3, 5], "qr": [3, -5], "t": 2}
//   ```
// D3 is published next to this file (widgets/assets.py); it defines the global d3
await import(new URL('d3.min.js', import.meta.url).href);
const d3 = globalThis.d3;
const { python, latestOnly, whenNear } = await import(new URL(`python.mjs?v=${performance.timeOrigin}`, import.meta.url).href);   // never a stale copy

const MARGIN = { top: 12, right: 12, bottom: 40, left: 46 };
const HMAX = 10, HUMAX = 15, XMAX = 10, TMAX = 5;      // the ranges of the original figure
const PANELS = [
  { title: 'Phase plane', xlabel: 'h', ylabel: 'hu', x: [0, HMAX], y: [-HUMAX, HUMAX] },
  { title: 'x-t plane', xlabel: 'x', ylabel: 't', x: [-XMAX, XMAX], y: [0, TMAX] },
  { title: 'Depth h at time t', xlabel: 'x', ylabel: 'h', x: [-XMAX, XMAX], y: [0, HMAX] },
  { title: 'Momentum hu at time t', xlabel: 'x', ylabel: 'hu', x: [-XMAX, XMAX], y: [-HUMAX, HUMAX] },
];

function render({ model, el }) {
  const params = { ql: [...model.get('ql')], qr: [...model.get('qr')], t: model.get('t') ?? 2 };

  el.classList.add('acoustics-explorer');
  const status = d3.select(el).append('div').attr('class', 'ae-status')
    .text('This figure becomes interactive when Python starts in your browser.');
  const svg = d3.select(el).append('svg').attr('role', 'img')
    .attr('aria-label', 'Shallow water phase plane and solution');
  const panels = PANELS.map((spec, i) => {
    const g = svg.append('g');
    const clipId = `sw-clip-${Math.random().toString(36).slice(2)}-${i}`;
    const clip = g.append('clipPath').attr('id', clipId).append('rect');
    g.append('g').attr('class', 'ae-xaxis');
    g.append('g').attr('class', 'ae-yaxis');
    g.append('text').attr('class', 'ae-xlabel').attr('text-anchor', 'middle').text(spec.xlabel);
    g.append('text').attr('class', 'ae-ylabel').attr('text-anchor', 'middle').text(spec.ylabel);
    g.append('text').attr('class', 'ae-title').attr('text-anchor', 'middle').text(spec.title);
    g.append('g').attr('class', 'ae-plot').attr('clip-path', `url(#${clipId})`);
    return { ...spec, g, clip };
  });
  let data = null;
  let size = null;

  // Two panels per row, or all four stacked on narrow screens
  function layout() {
    const width = el.clientWidth;
    const cols = width >= 520 ? 2 : 1;
    const w = width / cols, h = Math.min(w * 0.8, 320);
    const height = h * (4 / cols);
    svg.attr('width', width).attr('height', height).attr('viewBox', `0 0 ${width} ${height}`);
    panels.forEach((panel, i) => {
      const x0 = (i % cols) * w, y0 = Math.floor(i / cols) * h;
      const top = MARGIN.top + 14;
      panel.sx = d3.scaleLinear(panel.x, [MARGIN.left, w - MARGIN.right]);
      panel.sy = d3.scaleLinear(panel.y, [h - MARGIN.bottom, top]);
      panel.g.attr('transform', `translate(${x0},${y0})`);
      panel.clip.attr('x', MARGIN.left).attr('y', top)
        .attr('width', w - MARGIN.left - MARGIN.right).attr('height', h - top - MARGIN.bottom);
      panel.g.select('.ae-xaxis').attr('transform', `translate(0,${h - MARGIN.bottom})`).call(d3.axisBottom(panel.sx).ticks(5));
      panel.g.select('.ae-yaxis').attr('transform', `translate(${MARGIN.left},0)`).call(d3.axisLeft(panel.sy).ticks(5));
      panel.g.select('.ae-xlabel').attr('x', (MARGIN.left + w - MARGIN.right) / 2).attr('y', h - 6);
      panel.g.select('.ae-ylabel').attr('transform', `translate(12,${(h - MARGIN.bottom + top) / 2}) rotate(-90)`);
      panel.g.select('.ae-title').attr('x', (MARGIN.left + w - MARGIN.right) / 2).attr('y', MARGIN.top + 2);
    });
    size = { width, height };
    draw();
  }

  function draw() {
    if (!data || !size) return;
    const [pp, xt, ph, phu] = panels;
    const line = (panel, xs, ys) => d3.line().x((_, i) => panel.sx(xs[i])).y((_, i) => panel.sy(ys[i]))(xs);

    // Phase plane: shock (red) and rarefaction (blue) curves, the states and their labels
    pp.g.select('.ae-plot').selectAll('path').data(data.curves).join('path')
      .attr('class', d => `ae-line sw-${d.kind}` + (d.physical ? '' : ' ae-dashed'))
      .attr('d', d => line(pp, d.h, d.hu));
    const names = ['l', 'm', 'r'];
    const points = pp.g.select('.ae-plot').selectAll('g.ae-point').data(data.states).join(enter => {
      const g = enter.append('g').attr('class', (_, i) => i === 1 ? 'ae-point' : 'ae-point ae-drag')
        .attr('data-index', (_, i) => i);
      g.append('circle').attr('r', 7);
      g.append('text').attr('dx', 10).attr('dy', -8).html((_, i) =>
        `q<tspan baseline-shift="sub" font-size="75%">${names[i]}</tspan>`);
      return g;
    });
    points.attr('transform', d => `translate(${pp.sx(d[0])},${pp.sy(d[1])})`);
    points.filter('.ae-drag').call(dragState);

    // x-t plane: each wave (a rarefaction as a fan of 5 lines), and the time line with its handle
    const rays = data.speeds.flatMap((s, i) => (data.wave_types[i] === 'raref' && s.length === 2
      ? d3.range(5).map(k => ({ s: s[0] + (s[1] - s[0]) * k / 4, kind: 'raref' }))
      : [{ s: s[0], kind: data.wave_types[i] }]));
    xt.g.select('.ae-plot').selectAll('line.sw-ray').data(rays).join('line')
      .attr('class', d => `sw-ray sw-${d.kind}`)
      .attr('x1', xt.sx(0)).attr('y1', xt.sy(0))
      .attr('x2', d => xt.sx(d.s * TMAX)).attr('y2', xt.sy(TMAX));
    xt.g.select('.ae-plot').selectAll('line.sw-time').data([params.t]).join('line').attr('class', 'sw-time ae-dashed ae-line')
      .attr('x1', xt.sx(-XMAX)).attr('x2', xt.sx(XMAX)).attr('y1', d => xt.sy(d)).attr('y2', d => xt.sy(d));
    xt.g.select('.ae-plot').selectAll('circle.sw-handle').data([params.t]).join('circle')
      .attr('class', 'sw-handle ae-drag').attr('r', 7)
      .attr('cx', xt.sx(0.9 * XMAX)).attr('cy', d => xt.sy(d)).call(dragTime);

    // Depth and momentum at time t
    ph.g.select('.ae-plot').selectAll('path').data([data.h]).join('path').attr('class', 'ae-line').attr('d', d => line(ph, data.x, d));
    phu.g.select('.ae-plot').selectAll('path').data([data.hu]).join('path').attr('class', 'ae-line').attr('d', d => line(phu, data.x, d));
  }

  const update = latestOnly('shallow_water_explorer',
    () => ({ ...params, hmax: HMAX, xmax: XMAX }),
    result => { data = result; draw(); });
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const dragState = d3.drag().on('drag', function (event) {
    const which = this.dataset.index === '0' ? 'ql' : 'qr';
    const [pp] = panels;
    params[which] = [clamp(pp.sx.invert(event.x), 0.01, HMAX), clamp(pp.sy.invert(event.y), -HUMAX, HUMAX)];
    data.states[which === 'ql' ? 0 : 2] = params[which];
    draw();
    update();
  });
  const dragTime = d3.drag().on('drag', event => {
    params.t = clamp(panels[1].sy.invert(event.y), 0.01, TMAX);
    draw();
    update();
  });

  const resize = new ResizeObserver(layout);
  resize.observe(el);
  whenNear(el).then(() => {
    status.text('Starting Python in your browser…');
    return update();
  }).then(() => {
    status.text('Drag qₗ, qᵣ or the time. Computed in your browser with Python (exact_solvers/shallow_water.py).');
    el.dataset.state = 'ready';
  }).catch(error => {
    status.text('Python could not start, so this figure is not interactive: ' + error.message);
    el.dataset.state = 'error';
  });
  return () => resize.disconnect();
}

export default { render };
