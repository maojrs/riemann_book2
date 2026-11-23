# Riemann Problems and Jupyter Solutions — web edition (experimental)

[![Read the book](https://img.shields.io/badge/Read_the_book-online-2563eb?style=for-the-badge)](https://maojrs.github.io/riemann_book2/)
[![Download the notebooks](https://img.shields.io/badge/Download-notebooks-16a34a?style=for-the-badge)](https://github.com/maojrs/riemann_book2/releases/latest/download/riemann_book_notebooks.zip)

An experimental port of the book
[*Riemann Problems and Jupyter Solutions*](https://github.com/clawpack/riemann_book)
(D. I. Ketcheson, R. J. LeVeque and M. J. del Razo; SIAM, 2020) to
[Jupyter Book 2](https://jupyterbook.org): **[read the book here](https://maojrs.github.io/riemann_book2/)**.
The text and the science are the original ones; what is new is the way the book is built and
read:

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

**Status:** test release. All the chapters are converted; the web edition is being tested and
reviewed before its first release.

## Run the notebooks yourself

Get the notebooks, with the code they need to run, in either of these ways:

- download them with the **Download the notebooks** button above and unpack the .zip, or
- clone the `notebooks` branch:

  ```bash
  git clone --branch notebooks --single-branch https://github.com/maojrs/riemann_book2.git riemann_book_notebooks
  ```

Then, in that folder (Python 3.10 or newer):

```bash
pip install -e . jupyterlab
jupyter lab chapters/
```

These are plain Jupyter notebooks, without the files of the web edition; they are updated with
each release.

Each chapter can also be run online, with nothing to install: the rocket icon at the top right of
its page in the web book opens it on [Binder](https://mybinder.org) (the first start can take a
few minutes).

## Build the web book locally

With [uv](https://docs.astral.sh/uv/) and [Node.js](https://nodejs.org) installed, in a clone of
this repository:

```bash
uv sync                                  # the Python environment
uv run python widgets/assets.py          # files for the interactive figures
uv run jupyter-book start --execute      # preview at http://localhost:3000
```

`uv run pytest` runs the test suite. After changing the book's Python code, run
`uv run jupyter-book clean --execute -y` before the preview, so that the figures are computed
again.

## Repository structure

```
riemann_book2/
├── chapters/         the book's notebooks (the source of the book), and the references
│                     page with its bibliography (references.md, references.bib)
├── figures/          static images and the original phase-plane figures
├── exact_solvers/    the book's exact Riemann solvers and demo figures
├── utils/            riemann_tools (compute and plot Riemann solutions) and live_figure
│                     (interactive figures shared by the notebooks and the web)
├── miniclaw/         minimal pure-Python version of the PyClaw methods used in the book
├── widgets/          the interactive figures of the web book: the JavaScript that shows them
│   │                 and their controls on the page, and the Python that answers it in the
│   │                 reader's browser
│   └── figures/      one module per chapter: for each interactive cell, the figure the web
│                     book shows (the cell's plotting function, or a faster version that
│                     draws the same picture) and its controls (sliders, boxes, menus)
├── tests/            the test suite and reference results from the original book
│   └── widgets/      tests of the interactive figures (notebook and web book)
├── index.md          the home page
├── myst.yml          book configuration and table of contents
├── book.css          small style adjustments for the web
├── pyproject.toml    makes the code installable
├── CHANGES.md        every change with respect to the original book
└── .github/, .agents/   CI, and notes for the editors and agents
```

## License

The text is licensed under [CC BY-NC-ND 4.0](LICENSE-TEXT.md) and the code under the
[BSD 3-Clause license](LICENSE-CODE), as in the original book.
