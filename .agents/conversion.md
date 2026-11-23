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
   - Use a scratch copy of the project whose `myst.yml` lists only this chapter, with `uv run --project <repository> jupyter-book build --html --execute`.
   - Prepare the widget files first (`uv run python widgets/assets.py`: the wheel of the book's code, Pyodide and D3, published by `myst.yml`), and again after changing Python code that the web figures use.
   - The Jupyter server needs the venv on `PATH`: `uv run` provides it.
   - The build reuses a notebook's outputs while its code cells are unchanged (`_build/execute`), even when the Python code they call has changed. After changing `exact_solvers/`, `utils/`, `miniclaw/` or `widgets/figures/`, run `jupyter-book clean --execute -y` first, or the build-time pictures (and the placeholders of the interactive figures) stay old.
   - Citations: `[@key]` (or `{cite:p}` for keys with a colon); every entry of `chapters/references.bib` needs a `doi` (or a `url`). After changing citations or the bibliography, run `python3 .agents/tools/references_page.py` to update `chapters/references.md` (it lists every entry of `references.bib`).
   - New MyST markup in a chapter must also be handled by `.agents/tools/clean_notebooks.py` (the release notebooks): it stops on markup it does not know, and `tests/test_clean_notebooks.py` runs it.
7. Check for horizontal scroll bars (see below) at 390, 768, 1280, 1440 and 1920 px, and look at the screenshots.
8. Register the changes in `CHANGES.md`. Add any text that refers to things that no longer exist to "Text to flag for the authors" in `.agents/plan.md`.

## Conventions
- **Equations:**
  - Numbered environments (`align`, `equation`) stay exactly as written. A `\label{X}` inside them works in MyST.
  - Unnumbered displays (`align*`, `equation*`, `$$…$$`) become `{math}` blocks with `:enumerated: false`, with the LaTeX unchanged. MyST would otherwise number them, shifting all equation numbers.
  - MyST gives a math block one label and one number: an `align` with several `\label`s becomes one `align` per labelled row (the converter does it; the LaTeX of each row is unchanged).
  - A one-row `align` with at most one top-level `&` becomes an `equation` (a one-row `align*` an unnumbered `{math}` block), with that `&` removed. It looks the same, but KaTeX draws `align` as a table that cannot wrap, while an `equation` can break after an `=` when it is too long (`book.css`). Rows with two `&` (two equations side by side) stay `align`.
- **Equation references:** `(\ref{X})` and `\eqref{X}` become `` {eq}`X` ``, which renders as "(n)". A bare `\ref{X}` is reported, to decide by hand.
- **Citations:** cite2c `<cite data-cite="key">…</cite>` becomes `[@key]`. The key must exist in `chapters/references.bib`.
- **Equation labels are global** in the web book: a label defined in two chapters (copied text) is renamed in the later one, with its references.
- **Warnings printed by chapter code** that the original hid (e.g. through the old global warning filter) are hidden on the web with the cell tag `remove-stderr`; the code is not changed.
- **Links between notebooks** (`[Euler](Euler.ipynb)`) stay as they are: MyST resolves them.
- **Links to a heading** (`[the section above](Shallow_water.ipynb#Dam-break-problem:-all-shock-solution)`): give the heading a label line `(sw:dam-break-all-shock)=` and link to `#sw:dam-break-all-shock`. The converter warns about them.
- **Paths** are relative to `chapters/`: `../figures/…`, `../exact_solvers/…`.
- **`Image('figures/x.png', width=N)` code cells** become `{image}` blocks (`:width: Npx`, `:align: center`).
- **Phase-plane `IFrame(src='phase_plane/X.html', …)`** becomes `HTML(open('../figures/phase_plane/X.html').read())`. The converter adds `HTML` to the cell's `IPython.display` import.
  - IFrames of local files are not copied into the site and give a 404.
  - The HTML files carry a small added script that scales the mpld3 figure to the page width.
- **`%matplotlib` and `%config` magics** are removed. Import cells that only repeat names imported earlier are removed.
- **Interactive cells** (ipywidgets `interact`): the code cell stays as it is, so the notebook works in Jupyter, and its build-time figure is the fallback without JavaScript (`book.css` hides the widget placeholders). For the web, a markdown cell right after it shows the live figure:
  ````
  ```{anywidget} ../widgets/interact.mjs
  :css: ../widgets/interact.css
  {"figure": "widgets.figures.acoustics.PHASE_PLANE", "values": {"pl": 3, "ul": 2}, "setup": {...}}
  ```
  ````
  - `figure` is an `InteractiveFigure` (`utils/live_figure.py`) in `widgets/figures/<topic>.py` (one module per topic, named after the book's module it draws from: `burgers.py`, `shallow_water.py`, …; the book's `exact_solvers/*_demos.py` keep only their notebook code), with the cell's controls (labels exactly as the ipywidgets descriptions). Usually `InteractiveFigure.redraw(plotting_function, controls, factory=..., fixed=...)`: the book's own function, drawn again in full at each change. List the controls in the order interact shows them (the function's arguments); give `rows` only when the original lays its widgets out itself (HBox/VBox; `None` for an empty column). Use the original's widget kinds (`radio` for RadioButtons). For the most used figures, a `LiveFigure` class (fast), as in `acoustics_demos.py`.
  - `tests/widgets/test_interactive_cells.py` checks every widget cell against its code cell (controls, values, fixed arguments, picture); it must pass.
  - A cell that shows several interactive figures (e.g. `shallow_water.plot_riemann_SW`) gets one widget cell per figure, in order, with `"output": k` (the k-th image of the cell).
  - `values` repeats the values the code cell passes (for example `ql`, `qr`), `setup` the arguments of the figure class.
  - Figures drawn with JavaScript instead (drag explorers, `widgets/acoustics_explorer.mjs`) go in the same way, after the cell they replace on the web; tag that cell `remove-cell` if its output only works in Jupyter (mpld3).
  - These cells are markup: the prose check ignores them.
  - When the chapter defines the plotting function or the solvers it uses in its own code cells (Part II), copy them verbatim into the chapter's figure module (e.g. `widgets/figures/shallow_water_approximate.py`), with a function that returns the cell's plot function; the test checks the copy draws the same picture. Integer sliders: `slider(..., integer=True)`.
- **Code** in a chapter may be changed only if the change is small and the user approves it first; it may never alter what the chapter computes. Fixing warnings in the plotting code of `*_demos.py` is fine, as long as the figure is unchanged; register it in `CHANGES.md`.

## No horizontal scroll bars
Nothing on a page may scroll sideways at any width. That covers the whole page, equations, code, outputs and figures.
- Check with `.agents/tools/pagecheck.py` (instructions in its docstring). Widths below 500px are emulated with a frame of that width, since Firefox windows cannot be narrower; this is the real phone width (before, "390" measured 488px). It must report `page_hscroll=False`, `scrollers=0` and no "WIDER THAN WINDOW" lines at every width.
- **Fix the cause:**
  - general layout problems go in `book.css`, for every page;
  - a warning printed by the code is fixed in the code;
  - a fixed-width HTML figure is made to scale.
- **Already handled in `book.css`:**
  - KaTeX `align` blocks were 2px too wide (fixed by sizing equations to their content; they are re-centred with `!important`, because the theme sets `margin: 0 !important`);
  - long code lines wrap;
  - the title in the top bar shrinks on small screens;
  - ipywidgets placeholders are hidden.
  - display equations wrap at top-level relations when too long, and are 0.9em on phones;
  - animations shrink to the column;
  - headings clip the theme's link icon (it widened the page on phones).

## Text to flag for the authors (do not change it yourself)
References to things that no longer exist or have changed, for example:
- "in the notebook version, or on [this webpage](http://www.clawpack.org/riemann_book/...)";
- "using … PyClaw" (now miniclaw);
- links to `blob/FA16/...` on GitHub.
