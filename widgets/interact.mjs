// Slider figure: the web version of an interactive notebook cell.
//
// It shows an InteractiveFigure (utils/live_figure.py) drawn by Python in the browser, with
// the same controls as the notebook. MyST markup, in a markdown cell after the code cell:
//
//   ```{anywidget} ../widgets/interact.mjs
//   :css: ../widgets/interact.css
//   {"figure": "widgets.figures.acoustics.PHASE_PLANE",
//    "values": {"pl": 3, "ul": 2},          (optional: control values other than the defaults)
//    "setup": {...},                         (optional: arguments of the figure)
//    "output": 1}                            (optional: which image of the cell it replaces)
//   ```
//
// Python starts when the reader gets near the figure. Until it is ready, the figure made at
// build time (the output of the code cell above) is shown; without JavaScript it simply stays.
const { python, latestOnly, whenNear } = await import(new URL(`python.mjs?v=${performance.timeOrigin}`, import.meta.url).href);   // never a stale copy

const GREEK = { alpha: 'α', beta: 'β', gamma: 'γ', lambda: 'λ', rho: 'ρ', sigma: 'σ', epsilon: 'ε' };

// A label as written for ipywidgets: math between $...$ (simple LaTeX: "p_l", "p_{min}",
// "\rho") as text with a subscript, anything else as plain text
function labelElement(label) {
  const span = document.createElement('span');
  span.className = 'bi-name';
  const math = label.match(/^\$(.*)\$$/) ?? label.match(/^([a-z])$/i);    // a one-letter name is a symbol
  if (!math) {
    span.textContent = label;
    return span;
  }
  span.classList.add('bi-math');
  const text = math[1].replace(/\\([a-zA-Z]+)/g, (all, name) => GREEK[name] ?? name);
  const [base, sub] = text.split('_');
  span.append(base);
  if (sub) span.appendChild(document.createElement('sub')).textContent = sub.replace(/[{}]/g, '');
  return span;
}

// One control: its label (as the ipywidgets description), the control and, for a slider,
// its value. Checkboxes and radio buttons keep their labels after the box or dot.
function controlElement(c, onChange) {
  const row = document.createElement(c.kind === 'radio' ? 'div' : 'label');
  if (c.kind === 'checkbox') {
    const input = Object.assign(document.createElement('input'), { type: 'checkbox', checked: c.value });
    input.addEventListener('change', () => onChange(input.checked));
    row.className = 'bi-check';
    row.append(input, labelElement(c.label));
    return row;
  }
  row.appendChild(labelElement(c.label));
  let input, readout;
  if (c.kind === 'radio') {
    input = document.createElement('span');
    input.className = 'bi-options';
    row.setAttribute('role', 'radiogroup');
    const group = `bi-${Math.random().toString(36).slice(2)}`;
    for (const option of c.options) {
      const choice = input.appendChild(document.createElement('label'));
      const radio = Object.assign(document.createElement('input'),
        { type: 'radio', name: group, checked: option === c.value });
      radio.addEventListener('change', () => onChange(option));
      choice.append(radio, String(option));
    }
  } else if (c.kind === 'dropdown') {
    input = document.createElement('select');
    for (const option of c.options) {
      input.appendChild(new Option(option ?? 'None', JSON.stringify(option), false, option === c.value));
    }
    input.addEventListener('change', () => onChange(JSON.parse(input.value)));
  } else if (c.kind === 'slider') {
    input = Object.assign(document.createElement('input'),
      { type: 'range', min: c.min, max: c.max, step: c.step, value: c.value });
    readout = document.createElement('output');
    const show = value => {            // the value, and how far the track is filled
      readout.textContent = value.toFixed(c.integer ? 0 : 2);
      input.style.setProperty('--fill', (value - c.min) / (c.max - c.min));
    };
    // The start value as given: the browser puts the thumb on the nearest step from min
    // (600 becomes 600.01 when min is 0.01), as ipywidgets does only once it is moved
    show(c.value);
    input.addEventListener('input', () => { show(+input.value); onChange(+input.value); });
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

// The rows of controls as the notebook lays them out, grouped for the page: a time slider
// alone in its row spans the width ('time'); controls of one kind that the notebook shows
// one per line sit side by side as space allows ('flow'), checkboxes in one line
// ('checks'); rows of several controls (the function's own layout) keep their columns ('row').
function controlBlocks(rows, byName) {
  const blocks = [];
  for (const names of rows) {
    const c = names.length === 1 ? byName[names[0]] : null;
    const kind = !c ? 'row' : c.name === 't' && c.kind === 'slider' ? 'time'
      : c.kind === 'checkbox' ? 'checks' : 'flow';
    const last = blocks.at(-1);
    const joins = last && last.kind === kind && (kind === 'checks' || (kind === 'flow' && last.of === c.kind));
    if (joins) last.names.push(...names);
    else blocks.push({ kind, of: c?.kind, names: [...names] });
  }
  return blocks;
}

// The image output of the code cell above this widget (other widgets in between are
// skipped): its image number `output`, or the last one. null if there is none.
function buildTimeFigure(el, output) {
  let block = el.getRootNode().host ?? el;
  while (block.parentElement && !block.parentElement.matches('article')) block = block.parentElement;
  const isWidget = b => [...b.querySelectorAll('*')].some(e => e.shadowRoot);
  do { block = block.previousElementSibling; } while (block && isWidget(block));
  const images = [...(block?.querySelectorAll('img') ?? [])];
  return images[output ?? images.length - 1] ?? null;
}

// Figures are shown at 80% of their size in pixels (wide, short ones at 95%), at most 60%
// of the window high, and never wider than the column. Static outputs: book.css.
function setSize(element, width, height) {
  element.style.width = `${(width / height >= 1.6 ? 0.95 : 0.8) * width}px`;
  element.style.maxWidth = `min(100%, ${60 * width / height}vh)`;
}

function paint(canvas, { width, height, rgba }) {
  canvas.width = width;
  canvas.height = height;
  setSize(canvas, width, height);
  const pixels = new Uint8ClampedArray(rgba.buffer, rgba.byteOffset, rgba.byteLength);
  canvas.getContext('2d').putImageData(new ImageData(pixels, width, height), 0, 0);
}

async function render({ model, el }) {
  const figure = model.get('figure');
  const setup = model.get('setup') ?? null;
  el.classList.add('book-interact');
  const status = el.appendChild(Object.assign(document.createElement('div'),
    { className: 'bi-status', textContent: 'This figure becomes interactive when Python starts in your browser.' }));
  const form = el.appendChild(Object.assign(document.createElement('div'), { className: 'bi-controls' }));
  const placeholder = el.appendChild(document.createElement('img'));
  const canvas = el.appendChild(Object.assign(document.createElement('canvas'), { hidden: true }));

  const staticFigure = buildTimeFigure(el, model.get('output'));
  if (staticFigure) {
    placeholder.addEventListener('load', () => setSize(placeholder, placeholder.naturalWidth, placeholder.naturalHeight));
    placeholder.src = staticFigure.src;
    placeholder.alt = staticFigure.alt;
    (staticFigure.closest('.not-prose') ?? staticFigure).style.display = 'none';
  } else {
    placeholder.hidden = true;
  }

  try {
    await whenNear(el);
    status.textContent = 'Starting Python in your browser… the controls appear when it is ready.';
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
    // Rows of several controls all have as many columns as the widest one, so that the
    // controls have the same width, as in ipywidgets
    const addBlock = ({ kind, names }, parent, columns) => {
      const block = parent.appendChild(Object.assign(document.createElement('div'), { className: `bi-${kind}` }));
      block.style.setProperty('--columns', columns);
      for (const name of names) {          // None (undefined here): an empty column
        block.appendChild(name == null ? document.createElement('span')
          : controlElement(byName[name], value => { values[name] = value; redraw(); }));
      }
    };
    // A failed drawing (e.g. a solver that does not converge for these values) is said so,
    // instead of leaving the previous picture as if it were the answer
    const redraw = () => update().then(() => { status.hidden = true; }, error => {
      status.textContent = 'This figure could not be drawn for these values: ' + error.message.split('\n').at(-1);
      status.hidden = false;
    });
    await update();
    // The sliders' values in one column as wide as the longest one any slider can show
    // ("-25.00"), so that the rows keep their size as the values change
    const longest = Math.max(0, ...controls.filter(c => c.kind === 'slider')
      .flatMap(c => [c.min, c.max].map(v => v.toFixed(c.integer ? 0 : 2).length)));
    el.style.setProperty('--readout', `${longest + 0.5}ch`);
    const blocks = controlBlocks(rows, byName);
    const columns = Math.max(1, ...blocks.filter(b => b.kind === 'row').map(b => b.names.length));
    blocks.forEach(block => addBlock(block, form, columns));
    if (options.length) {
      const details = form.appendChild(document.createElement('details'));
      details.appendChild(document.createElement('summary')).textContent = 'Plot options';
      for (let i = 0; i < options.length; i += 2) addBlock({ kind: 'row', names: options.slice(i, i + 2) }, details, 2);
    }
    status.hidden = true;
    el.dataset.state = 'ready';
  } catch (error) {
    status.textContent = 'Python could not start, so this figure is not interactive: ' + error.message;
    el.dataset.state = 'error';
  }
}

export default { render };
