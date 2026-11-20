# Notebook conversion

Rule 1 in AGENTS.md applies: only markup changes, never the wording. Acoustics is the pilot.

## Procedure for one chapter
1. Keep a copy of the unconverted notebook (or take it from clawpack/riemann_book master).
2. Remove the temporary first cell (`execute: skip: true`) from `chapters/NAME.ipynb`. It keeps unconverted chapters from executing in the build.
   Also set the kernelspec to `python3` if it is `python2` (Nonlinear_elasticity, Pressureless_flow).
3. `uv run python .agents/tools/convert_notebook.py chapters/NAME.ipynb`
   - This applies the conventions below. It prints what it changed, plus warnings for anything to fix by hand.
4. Fix the warnings by hand (markup only).
5. `python .agents/tools/prose_diff.py ORIGINAL.ipynb chapters/NAME.ipynb` must report **0 differences** in the prose.
6. Build the chapter with execution and fix any errors or warnings in its output.
   - Use a scratch copy of the project whose `myst.yml` lists only this chapter, with `PATH=.venv/bin:$PATH jupyter-book build --html --execute`.
   - Prepare the widget files first (`uv run python widgets/assets.py`: the wheel of the book's code, Pyodide and D3, published by `myst.yml`), and again after changing Python code that the web figures use.
   - The Jupyter server needs the venv on `PATH`.
7. Check for horizontal scroll bars (see below) at 390, 768, 1280, 1440 and 1920 px, and look at the screenshots.
8. Register the changes in `CHANGES.md`. Add any text that refers to things that no longer exist to "Text to flag for the authors" in `.agents/plan.md`.

## Conventions
- **Equations:**
  - Numbered environments (`align`, `equation`) stay exactly as written. A `\label{X}` inside them works in MyST.
  - Unnumbered displays (`align*`, `equation*`, `$$…$$`) become `{math}` blocks with `:enumerated: false`, with the LaTeX unchanged. MyST would otherwise number them, shifting all equation numbers.
- **Equation references:** `(\ref{X})` and `\eqref{X}` become `` {eq}`X` ``, which renders as "(n)". A bare `\ref{X}` is reported, to decide by hand.
- **Citations:** cite2c `<cite data-cite="key">…</cite>` becomes `[@key]`. The key must exist in `references.bib`.
- **Links between notebooks** (`[Euler](Euler.ipynb)`) stay as they are: MyST resolves them.
- **Paths** are relative to `chapters/`: `../figures/…`, `../exact_solvers/…`.
- **`Image('figures/x.png', width=N)` code cells** become `{image}` blocks (`:width: Npx`, `:align: center`).
- **Phase-plane `IFrame(src='phase_plane/X.html', …)`** becomes `HTML(open('../figures/phase_plane/X.html').read())`.
  - IFrames of local files are not copied into the site and give a 404.
  - The HTML files carry a small added script that scales the mpld3 figure to the page width.
- **`%matplotlib` and `%config` magics** are removed. Import cells that only repeat names imported earlier are removed.
- **Interactive cells** (ipywidgets `interact`): the code cell stays as it is, so the notebook works in Jupyter, and its build-time figure is the fallback without JavaScript (`book.css` hides the widget placeholders). For the web, a markdown cell right after it shows the live figure:
  ````
  ```{anywidget} ../widgets/interact.mjs
  :css: ../widgets/interact.css
  {"figure": "exact_solvers.acoustics_demos.PHASE_PLANE", "values": {"pl": 3, "ul": 2}, "setup": {...}}
  ```
  ````
  - `figure` is an `InteractiveFigure` (`utils/live_figure.py`) in the chapter's demo module; write one for each interactive function, as in `acoustics_demos.py` (a `LiveFigure` class plus its controls), with tests against the original figure (`tests/test_acoustics_demos.py`).
  - `values` repeats the values the code cell passes (for example `ql`, `qr`), `setup` the arguments of the figure class.
  - Figures drawn with JavaScript instead (drag explorers, `widgets/acoustics_explorer.mjs`) go in the same way, after the cell they replace on the web; tag that cell `remove-cell` if its output only works in Jupyter (mpld3).
  - These cells are markup: the prose check ignores them.
- **Code** in a chapter may be changed only if the change is small and the user approves it first; it may never alter what the chapter computes. Fixing warnings in the plotting code of `*_demos.py` is fine, as long as the figure is unchanged; register it in `CHANGES.md`.

## No horizontal scroll bars
Nothing on a page may scroll sideways at any width. That covers the whole page, equations, code, outputs and figures.
- Check with `.agents/tools/pagecheck.py` (instructions in its docstring). It must report `page_hscroll=False`, `scrollers=0` and no "WIDER THAN WINDOW" lines at every width.
- **Fix the cause:**
  - general layout problems go in `book.css`, for every page;
  - a warning printed by the code is fixed in the code;
  - a fixed-width HTML figure is made to scale.
- **Already handled in `book.css`:**
  - KaTeX `align` blocks were 2px too wide (fixed by sizing equations to their content; they are re-centred with `!important`, because the theme sets `margin: 0 !important`);
  - long code lines wrap;
  - the title in the top bar shrinks on small screens;
  - ipywidgets placeholders are hidden.

## Text to flag for the authors (do not change it yourself)
References to things that no longer exist or have changed, for example:
- "in the notebook version, or on [this webpage](http://www.clawpack.org/riemann_book/...)";
- "using … PyClaw" (now miniclaw);
- links to `blob/FA16/...` on GitHub.
