"""Prepare the files the web book's widgets load, in _build/assets (published by myst.yml):

  - the book's code (exact_solvers, utils, miniclaw, widgets) as a wheel;
  - Pyodide (Python in the browser) with only the packages the widgets use;
  - D3, for the figures drawn in JavaScript.

Hosting them with the book keeps it working without any outside service. Run before building
the site (the CI does):

    uv run python widgets/assets.py

Downloads are checked against Pyodide's checksums and kept, so later runs only rebuild the wheel.
"""
import hashlib
import json
import pathlib
import subprocess
import urllib.request

PYODIDE_VERSION = '0.28.3'
PACKAGES = ['numpy', 'matplotlib', 'micropip']      # and everything they depend on
D3_VERSION = '7.9.0'

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / '_build' / 'assets'
PYODIDE_URL = f'https://cdn.jsdelivr.net/pyodide/v{PYODIDE_VERSION}/full/'
PYODIDE_CORE = ['pyodide.js', 'pyodide.asm.js', 'pyodide.asm.wasm', 'python_stdlib.zip', 'pyodide-lock.json']
D3_URL = f'https://cdn.jsdelivr.net/npm/d3@{D3_VERSION}/dist/d3.min.js'


def download(url, path, sha256=None):
    """Download url to path, unless it is already there (with the right checksum)."""
    if path.exists() and (sha256 is None or hashlib.sha256(path.read_bytes()).hexdigest() == sha256):
        return
    print('downloading', url)
    with urllib.request.urlopen(url) as response:
        data = response.read()
    if sha256 is not None and hashlib.sha256(data).hexdigest() != sha256:
        raise ValueError(f'checksum mismatch for {url}')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def with_dependencies(names, packages):
    """The packages in names and all the packages they depend on (from pyodide-lock.json)."""
    needed = set()
    while names:
        name = names.pop()
        if name not in needed:
            needed.add(name)
            names += packages[name]['depends']
    return sorted(needed)


def pyodide():
    folder = ASSETS / 'pyodide'
    for name in PYODIDE_CORE:
        download(PYODIDE_URL + name, folder / name)
    packages = json.loads((folder / 'pyodide-lock.json').read_text())['packages']
    for name in with_dependencies(list(PACKAGES), packages):
        package = packages[name]
        download(PYODIDE_URL + package['file_name'], folder / package['file_name'], package['sha256'])


def wheel():
    subprocess.run(['uv', 'build', '--wheel', '--out-dir', str(ASSETS), '--quiet'], cwd=ROOT, check=True)


if __name__ == '__main__':
    pyodide()
    download(D3_URL, ASSETS / 'd3.min.js')
    wheel()
    print('ready:', ASSETS)
