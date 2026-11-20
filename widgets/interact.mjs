// Slider figure: the web version of an interactive notebook cell.
//
// It shows an InteractiveFigure (utils/live_figure.py) drawn by Python in the browser, with
// the same controls as the notebook. MyST markup, in a markdown cell after the code cell:
//
//   ```{anywidget} ../widgets/interact.mjs
//   :css: ../widgets/interact.css
//   {"figure": "exact_solvers.acoustics_demos.PHASE_PLANE",
//    "values": {"pl": 3, "ul": 2},          (optional: control values other than the defaults)
//    "setup": {...}}                         (optional: arguments of the figure class)
//   ```
//
// Until Python is ready, the figure made at build time (the output of the code cell above)
// is shown in its place; without JavaScript that output simply stays.
const { python, latestOnly } = await import(new URL('python.mjs', import.meta.url).href);

const GREEK = { alpha: 'α', beta: 'β', gamma: 'γ', lambda: 'λ', rho: 'ρ', sigma: 'σ', epsilon: 'ε' };

// A simple LaTeX label ("p_l", "p_{min}", "\rho") as text with a subscript
function labelElement(latex) {
  const span = document.createElement('span');
  span.className = 'bi-name';
  const text = latex.replace(/\\([a-zA-Z]+)/g, (all, name) => GREEK[name] ?? name);
  const [base, sub] = text.split('_');
  span.append(base);
  if (sub) span.appendChild(document.createElement('sub')).textContent = sub.replace(/[{}]/g, '');
  return span;
}

function controlElement(c, onChange) {
  const row = document.createElement('label');
  row.appendChild(c.kind === 'dropdown' ? Object.assign(document.createElement('span'),
    { className: 'bi-name', textContent: c.label }) : labelElement(c.label));
  let input, readout;
  if (c.kind === 'dropdown') {
    input = document.createElement('select');
    for (const option of c.options) {
      input.appendChild(new Option(option ?? 'None', JSON.stringify(option), false, option === c.value));
    }
    input.addEventListener('change', () => onChange(JSON.parse(input.value)));
  } else if (c.kind === 'slider') {
    input = Object.assign(document.createElement('input'),
      { type: 'range', min: c.min, max: c.max, step: c.step, value: c.value });
    readout = document.createElement('output');
    readout.textContent = (+c.value).toFixed(2);
    input.addEventListener('input', () => { readout.textContent = (+input.value).toFixed(2); onChange(+input.value); });
  } else {
    input = Object.assign(document.createElement('input'), { type: 'number', step: 'any', value: c.value });
    if (c.min != null) Object.assign(input, { min: c.min, max: c.max });
    input.addEventListener('input', () => {
      if (input.value !== '' && input.checkValidity()) onChange(+input.value);
    });
  }
  row.className = readout ? 'bi-slider' : 'bi-wide';
  row.append(input);
  if (readout) row.append(readout);
  return row;
}

// The image output of the notebook cell just before this widget (null if none)
function buildTimeFigure(el) {
  let block = el.getRootNode().host ?? el;
  while (block.parentElement && !block.parentElement.matches('article')) block = block.parentElement;
  const images = block.previousElementSibling?.querySelectorAll('img') ?? [];
  return images[images.length - 1] ?? null;
}

function paint(canvas, { width, height, rgba }) {
  canvas.width = width;
  canvas.height = height;
  canvas.style.maxWidth = width + 'px';
  const pixels = new Uint8ClampedArray(rgba.buffer, rgba.byteOffset, rgba.byteLength);
  canvas.getContext('2d').putImageData(new ImageData(pixels, width, height), 0, 0);
}

async function render({ model, el }) {
  const figure = model.get('figure');
  const setup = model.get('setup') ?? null;
  el.classList.add('book-interact');
  const status = el.appendChild(Object.assign(document.createElement('div'),
    { className: 'bi-status', textContent: 'Starting Python in your browser… the controls appear in a few seconds.' }));
  const form = el.appendChild(Object.assign(document.createElement('div'), { className: 'bi-controls' }));
  const placeholder = el.appendChild(document.createElement('img'));
  const canvas = el.appendChild(Object.assign(document.createElement('canvas'), { hidden: true }));

  const staticFigure = buildTimeFigure(el);
  if (staticFigure) {
    placeholder.src = staticFigure.src;
    placeholder.alt = staticFigure.alt;
    (staticFigure.closest('.not-prose') ?? staticFigure).style.display = 'none';
  } else {
    placeholder.hidden = true;
  }

  try {
    const spec = await python('figure_controls', { figure });
    const { rows, options } = spec;
    // Python's None arrives as undefined; make it null, which survives JSON
    const controls = spec.controls.map(c => ({ ...c, value: c.value ?? null, options: c.options?.map(o => o ?? null) }));
    const values = Object.fromEntries(controls.map(c => [c.name, model.get('values')?.[c.name] ?? c.value]));
    const update = latestOnly('figure_frame', () => ({ figure, values, setup }), frame => {
      paint(canvas, frame);
      canvas.hidden = false;
      placeholder.hidden = true;
    });

    const byName = Object.fromEntries(controls.map(c => [c.name, { ...c, value: values[c.name] }]));
    const addRow = (names, parent) => {
      const row = parent.appendChild(Object.assign(document.createElement('div'), { className: 'bi-row' }));
      row.style.setProperty('--columns', names.length);
      for (const name of names) {
        row.appendChild(controlElement(byName[name], value => { values[name] = value; update(); }));
      }
    };
    await update();
    rows.forEach(names => addRow(names, form));
    if (options.length) {
      const details = form.appendChild(document.createElement('details'));
      details.appendChild(document.createElement('summary')).textContent = 'Plot options';
      for (let i = 0; i < options.length; i += 2) addRow(options.slice(i, i + 2), details);
    }
    status.textContent = 'Computed in your browser with Python.';
    el.dataset.state = 'ready';
  } catch (error) {
    status.textContent = 'Python could not start, so this figure is not interactive: ' + error.message;
    el.dataset.state = 'error';
  }
}

export default { render };
