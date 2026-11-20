# Riemann Problems and Jupyter Solutions — web edition (experimental)

[![Read the book](https://img.shields.io/badge/Read_the_book-online-2563eb?style=for-the-badge)](https://maojrs.github.io/riemann_book2/)
[![Download the notebooks](https://img.shields.io/badge/Download-notebooks-16a34a?style=for-the-badge)](https://github.com/maojrs/riemann_book2/releases/latest/download/riemann_book_notebooks.zip)

An experimental port of the book
[*Riemann Problems and Jupyter Solutions*](https://github.com/clawpack/riemann_book)
(D. I. Ketcheson, R. J. LeVeque and M. J. del Razo; SIAM, 2020) to
[Jupyter Book 2](https://jupyterbook.org). The text and the science are the original ones; what is
new is the way the book is built and read:

- **Interactive figures that run in the browser.** The book's own Python code runs in the reader's
  browser ([Pyodide](https://pyodide.org)), with a little JavaScript to draw and drag. No server,
  no Binder, no installation.
- **Pure Python.** The book's numerical examples, which used Clawpack/PyClaw, now run
  with `miniclaw`: a small educational implementation of just the finite-volume methods the book
  needs. It is not a substitute for Clawpack/PyClaw, which does much more.
- **A new, extensive test suite** (pytest) that checks the science: exact solutions,
  Rankine–Hugoniot and entropy conditions, conservation, convergence, and agreement with the
  original Clawpack results and figures.

This port was made with the help of AI coding agents.
All changes with respect to the original book are listed in [CHANGES.md](CHANGES.md).

**Status:** work in progress. The book structure and the Acoustics chapter are converted; the other
chapters follow one by one.

## Run the notebooks yourself

The **Download notebooks** button above gives the notebooks with only what they need to run in
Jupyter (*coming soon*). Until then, use the repository:

```bash
git clone https://github.com/maojrs/riemann_book2.git
cd riemann_book2
pip install -e .          # or: uv sync
jupyter lab chapters/     # needs JupyterLab or Notebook (pip install jupyterlab)
```

## Build the web book locally

With [uv](https://docs.astral.sh/uv/) and [Node.js](https://nodejs.org) installed:

```bash
uv sync                                   # Python environment
uv run pytest                             # test suite
uv run python widgets/assets.py           # files for the browser figures (Pyodide, D3, the book's code)
PATH=.venv/bin:$PATH uv run jupyter-book start --execute    # preview at http://localhost:3000
```

`jupyter-book build --html --execute` writes the static site to `_build/html`. On every push
to `main`, GitHub Actions runs the tests, builds the book and publishes it
([.github/workflows/book.yml](.github/workflows/book.yml)).

## Repository structure

```
riemann_book2/
├── chapters/         the book's notebooks (the source of the book)
├── figures/          static images and the original phase-plane figures
├── exact_solvers/    the book's exact Riemann solvers and demo figures
├── utils/            riemann_tools (compute and plot Riemann solutions) and live_figure
│                     (interactive figures shared by the notebooks and the web)
├── miniclaw/         minimal pure-Python version of the PyClaw methods used in the book
├── widgets/          browser side of the interactive figures (JavaScript + Python bridge)
│   └── figures/      each web figure: a notebook cell's plotting function and its controls
├── tests/            the test suite and reference results from the original book
│   └── widgets/      tests of the interactive figures (notebook and web book)
├── myst.yml          book configuration and table of contents
├── book.css          small style adjustments for the web
├── references.bib    bibliography
├── pyproject.toml    makes the code installable
├── CHANGES.md        every change with respect to the original book
└── .github/, .agents/   CI, and notes for the editors and agents
```

## License

The text is licensed under [CC BY-NC-ND 4.0](LICENSE-TEXT.md) and the code under the
[BSD 3-Clause license](LICENSE-CODE), as in the original book.
