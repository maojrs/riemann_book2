# Changes with respect to the original book

Every change compared with the original
[clawpack/riemann_book](https://github.com/clawpack/riemann_book), branch `master`, commit
`5b171f1` (30 Nov 2025). The `FA16` branch is the SIAM print version (2020). Changes to
`exact_solvers/` were approved by the authors.

## Text changes

- New front page `index.md` (title, authors, SIAM edition, about this web edition, license),
  replacing `Index.ipynb`/`Index2.ipynb`, whose chapter lists are now the book's navigation.
  **Draft, pending the authors' approval.**

## Bug fixes in the solvers

These don't affect any of the book's own examples.

- `nonlinear_elasticity.py`: 1-shocks had a positive speed and the 1-Hugoniot locus had the wrong
  sign, so the 1-wave went right and `fsolve` often failed. Now s = −√([σ]/(ρ[ε])) and
  u* = u_l + √([σ][ε]/ρ). Test: `test_nonlinear_elasticity.py`.
- `traffic_variable_speed.py`: with exactly equal fluxes and q_l > 1/2 > q_r, it returned a
  stationary expansion shock instead of the transonic rarefaction. Test:
  `test_traffic_variable_speed.py::test_equal_speed_limits_reduce_to_LWR`.
- `euler.py`: variable conversions ignored `gamma` and always used 1.4. Test:
  `test_euler.py::test_other_gamma`.
- `euler_tammann.py`: `primitive_to_conservative` used −γp∞ where the energy needs +γp∞. Test:
  `test_euler_tammann.py::test_primitive_conservative_round_trip`.
- `nonconvex.py`: `nonconvex_solutions` crashed without explicit `xi_left`/`xi_right`. Test:
  `test_nonconvex.py::test_nonconvex_solutions_with_default_xi_range`.

## Compatibility fixes

These make the code run on current Python, NumPy and IPython without changing any results.

- `euler.py`, `shallow_water.py`, `euler_tammann.py`, `interactive_pplanes.py`: take the scalar
  root from `fsolve`'s 1-element array (`p = p[0]`). NumPy ≥ 2.4 rejected it.
- `nonlinear_elasticity.py`, `interactive_pplanes.py`: LaTeX strings made raw (`r'$\gamma$'`).
- `utils/__init__.py`: no longer imports `nbtools`, which fails on IPython 9.
- `utils/riemann_tools.py`: removed the `__future__`, `six` and unused JSAnimation imports.
- `utils/riemann_tools.py`: `plot_characteristics` crashed (NumPy ≥ 2.4) when the characteristic
  speed function returns a 1-element array, as `traffic_LWR.c` does. The value is now squeezed.
  Test: `test_riemann_tools.py`.

## Interface changes

- `import utils` no longer auto-loads its submodules. Use `from utils import riemann_tools`, as the
  notebooks already do.
- `acoustics_demos.py`: two plot calls passed the colour twice (format `'-k'` and `color=`),
  which Matplotlib warns about and resolves in favour of `color=`. The format is now `'-'`. The
  figure is unchanged.
- Importing `exact_solvers.shallow_water` no longer silences all warnings: its
  `warnings.filterwarnings("ignore")` was removed (approved). The one expected warning it hid in the
  book (u = hu/h in dry regions, in `make_demo_plot_function`) is now silenced locally.
- PyClaw is replaced by miniclaw in `acoustics_demos.py`, `burgers_demos.py` and
  `shallow_water.macro_riemann_plot`: `from clawpack import pyclaw, riemann` became
  `from miniclaw import pyclaw, riemann`. No other change.
- Removed `utils` modules not used anywhere in the book: `animation_tools`, `jsanimate_widgets`,
  `snapshot_widgets`, `nbtools`, `fix_eqref`, `fix_nblinks`, `change_ql`.
- Removed unused or broken `riemann_tools` functions: `set_interact`, `plot_phase`, `plot_phase_3d`
  (it used a removed Matplotlib API), `JSAnimate_plot_riemann`, `waves_from_smoothness`, and the
  Clawpack doctest. `riemann_tools` now imports IPython only for `riemann_solution(verbose=True)`.
- `riemann_tools` imports matplotlib only inside the plotting functions, so computing a Riemann
  solution (e.g. in the browser) does not load it. Test: `test_computing_a_solution_does_not_load_matplotlib`.
- `riemann_tools.plot_characteristics` calls the speed function once per time step for all
  characteristics, instead of once per point (computing them is 5–12 times faster). Speed functions that only
  accept one point (e.g. `shallow_water.lambda_1`) are still called point by point. The
  integration is now `integrate_characteristics` and `characteristic_speeds`. Same
  characteristics: `test_vectorized_characteristics_match_the_point_by_point_loop`, `test_extra_lines_match_the_point_by_point_loop`.
- `riemann_tools.sample_riemann` (new) holds the sampling of the solution at time t, split out
  of `plot_riemann` unchanged, so interactive figures can reuse it. Test: `test_sample_riemann_puts_a_point_between_each_pair_of_waves`.
- `utils/live_figure.py` (new): `LiveFigure`, a matplotlib figure built once that redraws only
  what changes, and `InteractiveFigure`, a figure with its controls (sliders, number boxes,
  dropdowns) that gives both the notebook's ipywidgets and the web book's controls. In a
  notebook, moving a slider also only redraws what changed (16–29 ms per step instead of
  130–430 ms). Tests: `test_notebook_figure_is_built_once_and_updated`, `test_notebook_png_shows_the_web_frame`.
- `acoustics_demos.py`: the interactive figures (`decompose_q`, `char_solution`,
  `interactive_phase_plane`, `riemann_plot_pplane`) are rewritten on `utils/live_figure.py`,
  so the notebook and the web book draw them with the same code. Same functions and
  arguments; the figures are pixel-identical in the built Acoustics chapter. The notebook
  sliders are laid out in rows (`char_solution`: t, then ρ and K). `ipywidgets` and `IPython`
  are imported only by the notebook functions. Tests: `test_acoustics_demos.py`, against
  the previous module kept in `tests/reference/acoustics_demos_before.py`.

## Project infrastructure

- `README.md` (new): what this web edition is, how to run the notebooks and build the book, and
  the repository structure.
- `pyproject.toml` makes `exact_solvers`, `utils`, `miniclaw` and `widgets` installable (`uv sync` or
  `pip install -e .`).
- `tests/`: scientific test suite (pytest) for `exact_solvers`, `utils.riemann_tools` and `miniclaw`.
  It is not part of the deployed book.
- `tests/reference/`: results of the book's PyClaw runs with real Clawpack 5.14, made by
  `generate_reference.py` (needs Clawpack, not a book dependency), to test miniclaw against.
  The runs are defined once in `book_setups.py`, for both Clawpack and miniclaw.
- `miniclaw/` (new): pure-Python replacement for the PyClaw features the book uses
  (classic and SharpClaw solvers and all its Riemann solvers), with PyClaw's names (`from miniclaw import pyclaw, riemann`). It follows PyClaw's
  algorithm and step-size rule, and reproduces the book's Burgers, acoustics, shallow-water,
  Euler (FV_compare, including SharpClaw/WENO5), Kitchen-sink and variable-speed traffic runs
  exactly, and matches Clawpack's nonlinear elasticity f-wave solver pointwise. Tests: `test_miniclaw_*.py`.
  - `shallow_roe_tracer_1D`: Clawpack's Fortran version adds the tracer fluctuation through a stale
    loop index and an uninitialized `apdq`. miniclaw splits the tracer wave by the sign of its
    speed, as intended. It is only used by `shallow_water.macro_riemann_plot`, which no chapter calls.
- Book structure (Jupyter Book 2): `myst.yml` with the table of contents of `Index.ipynb` and
  `Index2.ipynb` (Parts I–VI; Part VI's two external nbviewer notebooks left out for now).
  The notebooks are in `chapters/`, copied from master with their outputs removed (the build
  regenerates them). Figures and phase-plane HTML are in `figures/`, `riemann.bib` is now
  `references.bib`, and `LICENSE-CODE` and `LICENSE-TEXT.md` are copied unchanged.
- `book.css`: a wider text column on large screens (each of the theme's six body columns up to
  14ch instead of 10ch, i.e. about 84 instead of 60 characters). The same columns are applied to
  the sidebar's own grid, so the sidebar and text never overlap (checked with screenshots at
  1280, 1440, 1600 and 1920 px).
- Chapters converted to MyST (markup only; a word-level check confirms the prose is unchanged):
  - **Part I:** Introduction, Advection, Acoustics, Burgers, Traffic_flow, Nonconvex_scalar,
    Shallow_water, Shallow_tracer, Euler.
  - What the conversion does is described in `.agents/conversion.md`:
    - equation references become `{eq}`;
    - citations become `[@key]`;
    - unnumbered displays are kept unnumbered;
    - an `align` with several `\label`s becomes one `align` per label (MyST gives a math block
      one label and one number; in Shallow_water the second labels were lost);
    - a one-row `align` (at most one `&`) becomes an `equation`, and a one-row `align*` plain
      display math: same look and numbers, but a long one can now break after an `=` on narrow
      screens instead of scrolling;
    - `Image` cells become `{image}`;
    - the phase-plane `IFrame` becomes embedded HTML (and `HTML` is added to the cell's
      `IPython.display` import); the acoustics phase plane is the drag explorer on the web
      (Introduction, Acoustics);
    - links to a heading of a notebook (`Shallow_water.ipynb#Dam-break-…`) get an explicit
      heading label;
    - paths are made relative to `chapters/`;
    - notebook magics and repeated import cells are removed.
  - The `python3` kernel is set where a notebook asked for `python2` (metadata only).
- Chapters not yet converted have a temporary first cell `execute: skip: true`, so the build
  (`--execute`) does not run them. Each is removed when its chapter is converted.
- `.gitattributes` marks `figures/phase_plane/*.html` as generated (and vendored) and `AGENTS.md` and `.agents/*.md`
  as documentation, so GitHub leaves them out of the repository's language statistics.
- `figures/phase_plane/*.html`: a short script appended to each file scales the figure to the
  page width.
- `book.css` also prevents horizontal scroll bars:
  - equations fit their box and are centred (the theme sets their margins to 0, which put them on the left);
  - long code lines wrap;
  - the top-bar title shrinks on small screens;
  - ipywidgets placeholders are hidden on the static site.
  - display equations can break after a top-level relation (=, <, …) when they are too long;
  - on phones (480px and less) display equations are the size of the text (0.9em instead of
    KaTeX's 1.21em);
  - animations (`to_jshtml`) shrink to the column (matplotlib fixes their slider at 374px);
  - headings clip the theme's link icon, which is shifted 10px to the right and widened the page
    on phones when a heading reached the edge.
- Interactive figures on the web (`widgets/`, new): the book's own Python runs in the reader's
  browser (Pyodide, in one worker per page, `widgets/python.mjs`), installed from the wheel that
  `myst.yml` publishes with the site (`static_files`). Before Python is ready the build-time figure
  is shown; without JavaScript it stays. Tests for the Python side: `test_widgets_compute.py`.
  - `interact.mjs`: the live version of an interactive cell, with the notebook's controls
    (`utils/live_figure.InteractiveFigure`), drawn by the same code as in the notebook.
  - `acoustics_explorer.mjs`: drag q_l and q_r in the acoustics phase plane (D3 drawing,
    `exact_solvers.acoustics` solution). It replaces the mpld3 figure on the web; the mpld3
    files stay, for the notebooks in Jupyter.
  - Acoustics: one markdown cell (`{anywidget}`) after each of its five interactive cells and
    after the mpld3 figure, whose cell is tagged `remove-cell` (it only works in Jupyter).
  - Part I: every interactive cell of Introduction, Advection, Burgers, Traffic_flow,
    Nonconvex_scalar, Shallow_water, Shallow_tracer and Euler (56 figures) is live on the web
    too, with the cell's controls. They are drawn by the book's own plotting functions, again
    in full at each change (`utils.live_figure.RedrawFigure`, 0.2–1 s per change). Each figure
    is described (controls, rows) in the chapter's demo module: `advection_demos.py` (new),
    `burgers_demos.py`, `traffic_demos.py`, `nonconvex_demos.py` (with the chapter's fluxes,
    named), `shallow_demos.py`, `euler_demos.py`; a few small functions there give the
    plotting function a cell builds (e.g. `euler_demos.riemann_solution_plot`). Notebook code
    is unchanged. Test: `test_interactive_cells.py` runs each chapter and checks that every web
    figure has the cell's controls, values and fixed arguments, and draws the same picture.
  - `shallow_water_explorer.mjs` (new): drag q_l, q_r in the h-hu plane and the time in the
    x-t plane (Hugoniot loci and integral curves, middle state, waves, depth and momentum at t;
    `exact_solvers.shallow_water` solution). It replaces the mpld3 shallow-water figure on the
    web in Introduction and Shallow_water (that cell is tagged `remove-cell`; the file stays for
    Jupyter). Test: `test_shallow_water_explorer_is_the_exact_solution`.
  - In the browser, modules that import ipywidgets or IPython (notebook only) get empty
    stand-ins, and a missing package (scipy for some chapters) is loaded when first needed.
  - `widgets/assets.py` prepares what the widgets load, in `_build/assets`: the wheel of the
    book's code, Pyodide 0.28.3 with only the packages used (numpy, matplotlib, scipy,
    micropip and their dependencies; checksums verified) and D3 7.9.0. They are hosted with the
    book (about 40 MB), so it does not depend on an outside service.
  - Pyodide is loaded from the jsDelivr CDN, which is much faster than GitHub Pages for large
    files, and from the book's own copy if the CDN fails. Package downloads cut short are
    retried. Python only starts when the reader gets near an interactive figure.
  - `python.mjs` and the wheel have fixed names, so the widgets load them in a way that never
    uses an old cached copy (otherwise a new widget could meet an old `python.mjs`).
- CI (`.github/workflows/book.yml`): on every push and pull request, runs the tests, prepares
  the widget files and builds the book with `--execute`; pushes to `main` are published on
  GitHub Pages.
- `.agents/tools/`: the conversion script, a prose check and a browser check for horizontal scroll
  bars. These are for the editors; they are not part of the book. The browser check emulates phone widths below 500px
  with a frame of that width (Firefox windows cannot be narrower than 500px, so "390px" used to
  measure 488px). With `--live` it first makes every interactive figure live.
- Not carried over: `make_html.py`, `make_pdf.py`, `make_html_bib.sh`, the Docker files, `html/`,
  `files_for_*`, `html_animations/`, `Index.ipynb`, `Index2.ipynb`, `Make_html_animations.ipynb`.
