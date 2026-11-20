// Python in the reader's browser: one Pyodide worker per page, shared by every figure.
//
//   python(fn, kwargs) calls widgets.compute.<fn>(**kwargs) and resolves with its result.
//   latestOnly(...)    makes an update function that never queues up stale requests.
//
//   whenNear(el)       resolves when el is about one screen away, so that Python is only
//                      started for readers who reach an interactive figure.
//
// The widgets import this file as python.mjs?v=<page load time>: its name is fixed, so
// without that a browser could use an old cached copy with newer widgets.
//
// Pyodide comes from the jsDelivr CDN, which is fast; if that fails, from the copy published
// with the book (prepared by widgets/assets.py, myst.yml static_files). The book's own code
// (exact_solvers, utils, miniclaw, widgets) is a wheel published next to this file.
// matplotlib is only loaded when a figure needs it, since it takes most of the start-up time.
const PYODIDE_VERSION = '0.28.3';      // the same as in widgets/assets.py
const SOURCES = [`https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`,
                 new URL('pyodide/', import.meta.url).href];
const WHEEL_NAME = 'riemann_book-0.1.0-py3-none-any.whl';
const WHEEL = new URL(WHEEL_NAME, import.meta.url).href;
const NEEDS_MATPLOTLIB = ['figure_controls', 'figure_frame'];   // they import plotting code

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

// Run Python code with its own local variables (requests from several figures can overlap
// while a package loads); a module missing in the browser (e.g. scipy for some chapters) is
// loaded from Pyodide's packages and the code is run again
async function run(py, code, locals) {
  const loaded = new Set();
  for (;;) {
    try { return py.runPython(code, { locals }); }
    catch (error) {
      const missing = /No module named '([\\w]+)/.exec(error.message)?.[1];
      if (!missing || loaded.has(missing)) throw error;
      loaded.add(missing);
      await loadPackages(py, [missing]);
    }
  }
}

async function startFrom(indexURL) {
  importScripts(indexURL + 'pyodide.js');
  const py = await loadPyodide({ indexURL });
  await loadPackages(py, ['numpy', 'micropip']);
  // Some of the book's modules import ipywidgets and IPython for their notebook versions only;
  // the browser does not need them, so they get empty stand-ins
  py.runPython([
    'import sys, types',
    "for name in ['ipywidgets', 'IPython', 'IPython.display']:",
    '    module = types.ModuleType(name)',
    '    module.__getattr__ = lambda attr: (lambda *args, **kwargs: None)',
    '    sys.modules[name] = module',
  ].join('\\n'));
  // The book's code: checked with the server each time ('no-cache'), so a new version of
  // the book is never mixed with an old copy in the browser's cache
  const wheel = await fetch('${WHEEL}', { cache: 'no-cache' });
  if (!wheel.ok) throw new Error('could not download the book\\'s code (' + wheel.status + ')');
  py.FS.writeFile('/tmp/${WHEEL_NAME}', new Uint8Array(await wheel.arrayBuffer()));
  await py.pyimport('micropip').install.callKwargs('emfs:/tmp/${WHEEL_NAME}', { deps: false });
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
    const locals = py.toPy({ kwargs_json: JSON.stringify(kwargs) });
    let result;
    try { result = await run(py, 'compute.' + fn + '(**json.loads(kwargs_json))', locals); }
    finally { locals.destroy(); }
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
