// Python in the reader's browser: one Pyodide worker per page, shared by every figure.
//
//   python(fn, kwargs) calls widgets.compute.<fn>(**kwargs) and resolves with its result.
//   latestOnly(...)    makes an update function that never queues up stale requests.
//
//   whenNear(el)       resolves when el is about one screen away, so that Python is only
//                      started for readers who reach an interactive figure.
//
// Pyodide comes from the jsDelivr CDN, which is fast; if that fails, from the copy published
// with the book (prepared by widgets/assets.py, myst.yml static_files). The book's own code
// (exact_solvers, utils, miniclaw, widgets) is a wheel published next to this file.
// matplotlib is only loaded when a figure needs it, since it takes most of the start-up time.
const PYODIDE_VERSION = '0.28.3';      // the same as in widgets/assets.py
const SOURCES = [`https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`,
                 new URL('pyodide/', import.meta.url).href];
const WHEEL = new URL('riemann_book-0.1.0-py3-none-any.whl', import.meta.url).href;
const NEEDS_MATPLOTLIB = ['figure_controls', 'figure_frame', 'render_figure'];   // they import plotting code

const WORKER_SOURCE = `
let ready, matplotlib;

// Pyodide only logs a package that fails to load. A download cut short is retried (already
// loaded packages are skipped); after three failures, stop with Pyodide's message.
async function loadPackages(py, names) {
  for (let attempt = 1; ; attempt++) {
    const errors = [];
    await py.loadPackage(names, { errorCallback: message => errors.push(message) });
    if (!errors.length) return;
    if (attempt === 3) throw new Error(errors.join(' '));
  }
}

async function startFrom(indexURL) {
  importScripts(indexURL + 'pyodide.js');
  const py = await loadPyodide({ indexURL });
  await loadPackages(py, ['numpy', 'micropip']);
  await py.pyimport('micropip').install.callKwargs('${WHEEL}', { deps: false });
  py.runPython("import os, json; os.environ['MPLBACKEND'] = 'Agg'; from widgets import compute");
  return py;
}

async function start() {
  const failures = [];
  for (const source of ${JSON.stringify(SOURCES)}) {
    try { return await startFrom(source); }
    catch (error) { failures.push(source + ': ' + error.message); }
  }
  throw new Error(failures.join(' | '));
}

onmessage = async ({ data: { id, fn, kwargs } }) => {
  try {
    const py = await (ready ??= start());
    if (${JSON.stringify(NEEDS_MATPLOTLIB)}.includes(fn)) await (matplotlib ??= loadPackages(py, ['matplotlib']));
    py.globals.set('kwargs_json', JSON.stringify(kwargs));
    let result = py.runPython('compute.' + fn + '(**json.loads(kwargs_json))');
    if (result?.toJs) {
      const proxy = result;
      result = proxy.toJs({ dict_converter: Object.fromEntries });
      proxy.destroy();
    }
    postMessage({ id, result }, result?.rgba ? [result.rgba.buffer] : []);
  } catch (error) {
    postMessage({ id, error: String(error.message ?? error) });
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

// Resolves when el comes within about one screen height of the visible part of the page
export function whenNear(el) {
  return new Promise(resolve => {
    const observer = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting)) {
        observer.disconnect();
        resolve();
      }
    }, { rootMargin: '100% 0px' });
    observer.observe(el);
  });
}
