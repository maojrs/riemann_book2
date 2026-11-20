// Acoustics phase-plane explorer: drag q_l and q_r in the p-u plane and see the middle
// state and the solution at time t. The Riemann solution is computed by the book's exact
// solver (exact_solvers/acoustics.py, through widgets/compute.py) running in the browser;
// D3 draws it. MyST markup:
//
//   ```{anywidget} ../widgets/acoustics_explorer.mjs
//   :css: ../widgets/acoustics_explorer.css
//   {"ql": [-2, 2], "qr": [0, -3], "rho": 1, "bulk": 4, "t": 1, "range": 5}
//   ```
// D3 is published next to this file (widgets/assets.py); it defines the global d3
await import(new URL('d3.min.js', import.meta.url).href);
const d3 = globalThis.d3;
const { python, latestOnly, whenNear } = await import(new URL('python.mjs', import.meta.url).href);

const MARGIN = { top: 12, right: 12, bottom: 40, left: 46 };

function render({ model, el }) {
  const params = {
    ql: [...model.get('ql')], qr: [...model.get('qr')],
    rho: model.get('rho'), bulk: model.get('bulk'), t: model.get('t'),
  };
  const range = model.get('range') ?? 5;     // all three plots use [-range, range]

  el.classList.add('acoustics-explorer');
  const status = d3.select(el).append('div').attr('class', 'ae-status')
    .text('This figure becomes interactive when Python starts in your browser.');
  const svg = d3.select(el).append('svg').attr('role', 'img')
    .attr('aria-label', 'Acoustics phase plane and solution');
  const panels = ['Phase plane', 'Pressure', 'Velocity'].map((title, i) => {
    const g = svg.append('g');
    const clipId = `ae-clip-${Math.random().toString(36).slice(2)}-${i}`;
    const clip = g.append('clipPath').attr('id', clipId).append('rect');
    g.append('g').attr('class', 'ae-xaxis');
    g.append('g').attr('class', 'ae-yaxis');
    g.append('text').attr('class', 'ae-xlabel').attr('text-anchor', 'middle');
    g.append('text').attr('class', 'ae-ylabel').attr('text-anchor', 'middle');
    g.append('g').attr('class', 'ae-plot').attr('clip-path', `url(#${clipId})`);
    return { title, g, clip };
  });
  let data = null;
  let size = null;

  // Phase plane on the left with pressure and velocity stacked on the right,
  // or all three stacked on narrow screens.
  function layout() {
    const width = el.clientWidth;
    let rects, height;
    if (width >= 520) {
      height = Math.min(width / 2, 380);
      rects = [[0, 0, width / 2, height], [width / 2, 0, width / 2, height / 2], [width / 2, height / 2, width / 2, height / 2]];
    } else {
      const h = Math.min(width * 0.75, 300);
      height = 3 * h;
      rects = [0, 1, 2].map(i => [0, i * h, width, h]);
    }
    svg.attr('width', width).attr('height', height).attr('viewBox', `0 0 ${width} ${height}`);
    panels.forEach((panel, i) => {
      const [x0, y0, w, h] = rects[i];
      panel.x = d3.scaleLinear([-range, range], [MARGIN.left, w - MARGIN.right]);
      panel.y = d3.scaleLinear([-range, range], [h - MARGIN.bottom, MARGIN.top]);
      panel.g.attr('transform', `translate(${x0},${y0})`);
      panel.clip.attr('x', MARGIN.left).attr('y', MARGIN.top)
        .attr('width', w - MARGIN.left - MARGIN.right).attr('height', h - MARGIN.top - MARGIN.bottom);
      const ticks = h < 220 ? 3 : 5;
      panel.g.select('.ae-xaxis').attr('transform', `translate(0,${h - MARGIN.bottom})`).call(d3.axisBottom(panel.x).ticks(5));
      panel.g.select('.ae-yaxis').attr('transform', `translate(${MARGIN.left},0)`).call(d3.axisLeft(panel.y).ticks(ticks));
      panel.g.select('.ae-xlabel').attr('x', (MARGIN.left + w - MARGIN.right) / 2).attr('y', h - 6)
        .text(i === 0 ? 'Pressure' : 'x');
      panel.g.select('.ae-ylabel').attr('transform', `translate(12,${(h - MARGIN.bottom + MARGIN.top) / 2}) rotate(-90)`)
        .text(i === 0 ? 'Velocity' : panel.title);
    });
    size = { width, height };
    draw();
  }

  function draw() {
    if (!data || !size) return;
    const [pp, pq, pu] = panels;
    const line = (panel, xs, ys) => d3.line().x((_, i) => panel.x(xs[i])).y((_, i) => panel.y(ys[i]))(xs);

    // Phase plane: eigenvector lines, the three states, and their labels
    pp.g.select('.ae-plot').selectAll('path').data(data.lines).join('path')
      .attr('class', d => d.physical ? 'ae-line' : 'ae-line ae-dashed')
      .attr('d', d => line(pp, d.p, d.u));
    const names = ['q_l', 'q_m', 'q_r'];
    const points = pp.g.select('.ae-plot').selectAll('g.ae-point').data(data.states).join(enter => {
      const g = enter.append('g').attr('class', (_, i) => i === 1 ? 'ae-point' : 'ae-point ae-drag')
        .attr('data-index', (_, i) => i);
      g.append('circle').attr('r', 7);
      g.append('text').attr('dx', 10).attr('dy', -8).html((_, i) =>
        `q<tspan baseline-shift="sub" font-size="75%">${names[i][2]}</tspan>`);
      return g;
    });
    points.attr('transform', d => `translate(${pp.x(d[0])},${pp.y(d[1])})`);
    points.filter('.ae-drag').call(drag);

    // Pressure and velocity at time t
    pq.g.select('.ae-plot').selectAll('path').data([data.p]).join('path').attr('class', 'ae-line').attr('d', d => line(pq, data.x, d));
    pu.g.select('.ae-plot').selectAll('path').data([data.u]).join('path').attr('class', 'ae-line').attr('d', d => line(pu, data.x, d));
  }

  // Dragging q_l or q_r moves the point at once; the solution follows as soon as Python
  // has computed it.
  const update = latestOnly('acoustics_explorer',
    () => ({ ...params, xmin: -range, xmax: range, pmin: -range, pmax: range }),
    result => { data = result; draw(); });
  const drag = d3.drag().on('drag', function (event) {
    const index = this.dataset.index === '0' ? 'ql' : 'qr';
    const [pp] = panels;
    const clamp = v => Math.max(-range, Math.min(range, v));
    params[index] = [clamp(pp.x.invert(event.x)), clamp(pp.y.invert(event.y))];
    data.states[index === 'ql' ? 0 : 2] = params[index];
    draw();
    update();
  });

  const resize = new ResizeObserver(layout);
  resize.observe(el);
  whenNear(el).then(() => {
    status.text('Starting Python in your browser…');
    return update();
  }).then(() => {
    status.text('Drag qₗ or qᵣ. Computed in your browser with Python (exact_solvers/acoustics.py).');
    el.dataset.state = 'ready';
  }).catch(error => {
    status.text('Python could not start, so this figure is not interactive: ' + error.message);
    el.dataset.state = 'error';
  });
  return () => resize.disconnect();
}

export default { render };
