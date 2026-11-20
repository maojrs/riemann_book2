// Python in the reader's browser: one Pyodide worker per page, shared by every figure.
//
//   python(fn, kwargs) calls widgets.compute.<fn>(**kwargs) and resolves with its result.
//   latestOnly(...)    makes an update function that never queues up stale requests.
//
// Pyodide and the book's own code (exact_solvers, utils, miniclaw, widgets, as a wheel) are
// published next to this file (myst.yml, static_files; prepared by widgets/assets.py).
// matplotlib is only loaded when a figure needs it, since it takes most of the start-up time.
const PYODIDE = new URL('pyodide/', import.meta.url).href;
const WHEEL = new URL('riemann_book-0.1.0-py3-none-any.whl', import.meta.url).href;
const NEEDS_MATPLOTLIB = ['figure_controls', 'figure_frame', 'render_figure'];   // they import plotting code

const WORKER_SOURCE = `
importScripts('${PYODIDE}pyodide.js');
let ready, matplotlib;
async function start() {
  const py = await loadPyodide({ indexURL: '${PYODIDE}' });
  await py.loadPackage(['numpy', 'micropip']);
  await py.pyimport('micropip').install.callKwargs('${WHEEL}', { deps: false });
  py.runPython("import os, json; os.environ['MPLBACKEND'] = 'Agg'; from widgets import compute");
  return py;
}
onmessage = async ({ data: { id, fn, kwargs } }) => {
  try {
    const py = await (ready ??= start());
    if (${JSON.stringify(NEEDS_MATPLOTLIB)}.includes(fn)) await (matplotlib ??= py.loadPackage('matplotlib'));
    py.globals.set('kwargs_json', JSON.stringify(kwargs));
    let result = py.runPython('compute.' + fn + '(**json.loads(kwargs_json))');
    if (result?.toJs) {
      const proxy = result;
      result = proxy.toJs({ dict_converter: Object.fromEntries });
      proxy.destroy();
    }
    postMessage({ id, result }, result?.rgba ? [result.rgba.buffer] : []);
  } catch (error) {
    postMessage({ id, error: String(error) });
  }
};`;

let worker = null;
let nextId = 0;
const pending = new Map();

export function python(fn, kwargs = {}) {
  if (!worker) {
    worker = new Worker(URL.createObjectURL(new Blob([WORKER_SOURCE], { type: 'text/javascript' })));
    worker.onmessage = ({ data }) => {
      const { resolve, reject } = pending.get(data.id);
      pending.delete(data.id);
      data.error ? reject(new Error(data.error)) : resolve(data.result);
    };
  }
  const id = nextId++;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    worker.postMessage({ id, fn, kwargs });
  });
}

// Each figure asks for its next picture only after the previous one has arrived, always
// with the latest values, so fast slider or mouse movements never queue up.
export function latestOnly(fn, kwargsOf, onResult) {
  let busy = false, again = false;
  return async function update() {
    if (busy) { again = true; return; }
    busy = true;
    try { onResult(await python(fn, kwargsOf())); }
    finally { busy = false; }
    if (again) { again = false; update(); }
  };
}
