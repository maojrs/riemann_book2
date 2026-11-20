# Changes with respect to the original book

Every change compared with the original
[clawpack/riemann_book](https://github.com/clawpack/riemann_book), branch `master`, commit
`5b171f1` (30 Nov 2025). The `FA16` branch is the SIAM print version (2020). Changes to
`exact_solvers/` were approved by the authors.

## Text changes

- New front page `index.md` (title, authors, SIAM edition, about this web edition: figures in
  the browser, faster plotting, pure Python, tests; license),
  replacing `Index.ipynb`/`Index2.ipynb`, whose chapter lists are now the book's navigation.
  **Draft, pending the authors' approval.**
- Approximate_solvers: the title "Part II.  Approximate Riemann Solvers" is "Approximate Riemann
  Solvers" (user's request): the part is already named in the table of contents.

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
- `euler.py` (approved): for strong collisions of a heavy, low-pressure gas (e.g. in
  `euler_demo1`'s ranges) `fsolve` did not converge from its two-rarefaction guess, printed a
  warning and returned a wrong middle state. When both `fsolve` attempts fail and φ(0) > 0,
  the middle pressure is now found by Brent's method on a bracket (φ decreases with p). Of a
  32,400-point grid over `euler_demo1`'s ranges, 254 cases failed and 220 now solve; solutions
  that converged before are unchanged. The other 34 are near vacuum, where the solver's
  vacuum test and its integral curves slightly disagree; they still warn. Test:
  `test_euler.py::test_strong_collisions` (two shocks, jump conditions, conservation).

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
- Plotting functions with a time slider draw on a live figure (`utils.live_figure.TimeFigure`,
  new): the figure is built once for the other values, and moving t only redraws what
  depends on it (time lines, solution curves, stripes, titles). Same names, arguments and
  pictures; in a notebook the function shows the figure as an image, and the web book draws
  `function.live_figure()`. Each drawing function is split into the part drawn once and an
  inner `at_time(t)`, with its original lines; `plt.` calls on the current axes became calls
  on the axes. A notebook slider step takes 17–26 ms instead of 245–430 ms (80–100 ms instead
  of 390–590 ms for the figures with stripes).
  - `riemann_tools.make_plot_function` (`utils/riemann_figure.py`, new): Advection, Burgers,
    Euler, Acoustics and the chapters of Parts II–V that use it. Test: `test_riemann_figure.py`,
    against the previous version in `tests/reference/riemann_tools_before.py` (at most 0.005%
    of the pixels differ).
  - `burgers.plot_riemann`, `traffic_LWR.plot_riemann_traffic`, `traffic_demos.jam` and
    `green_light`, `nonconvex_demos.make_plot_function` and `make_plot_function_qsliders`,
    `shallow_water.make_demo_plot_function` (also the stripes of `plot_riemann_SW`), and
    `euler_demos.plot_with_stripes`. Test: `test_time_figures.py`, against the previous
    versions in `tests/reference/plotting_before.py`.
  - `riemann_tools.plot_riemann` takes an optional `fig` to make its axes on;
    `nonconvex_demos.plot_waves` labels its own axes instead of pyplot's current ones.
- `euler_demos.plot_with_stripes`: the vertical axes hold every value of the solution, at all
  times, so they no longer move with t and the curves always fit; the tracer stripes cover the
  whole domain at all times (the particle paths now start far enough out, at the same spacing,
  and adjacent stripes touch); at t = 0 the pressure is now that of the initial states (the
  energy row was never set, the momentum row twice). The stripes are drawn as one collection
  of the same polygons. Tests: `test_euler_stripes_stay_inside_their_axes`,
  `test_euler_stripes_cover_the_domain`, `test_euler_stripes_at_time_zero_are_the_initial_states`.
- `euler_demo1`: the time slider is on top, full width, and every slider only redraws the
  solution (`euler_demos.stripes_demo`): the vertical ranges stay put while the solution fits
  them and fills a quarter of them, so dragging is smooth (about 40 ms a step instead of
  340–600 ms). Test: `test_euler_demo_axes_do_not_follow_small_changes`.
- Euler chapter, two code cells (approved): the checkboxes of `plot_integral_curves` and
  `plot_hugoniot_loci` are named '1-wave curves'/'3-wave curves' and 'Plot 1-loci'/'Plot
  3-loci', as in Shallow_water, instead of interact's `plot_1`/`plot_3`.
- Review fixes (2026-11-20):
  - Shallow_water: `shallow_demos.compare_curves` has a fixed vertical range (−10 to 10, as
    `connect_states`), so the axes do not jump with the sliders; `plot_riemann_SW` shows the
    velocity on −2.3 to 2.3 instead of −2 to 2, so velocities of ±1.9 and the dry-bed front
    (u = 2) are not on the edge.
    In its two examples with a dry state (`np.min(states[0]) == 0`) the depth is shown on 0 to
    2.5 instead of 0 to 4.5, since they are shallow.
  - Shallow_water on the web: the sliders of `connect_states` and of the last cell
    (`plot_exact_riemann_solution`) are in two columns, left state and right state (time on its
    own line), instead of one per line packed into three columns. `test_interactive_cells.py`
    lets a web figure pair interact's one-per-line controls in rows (every control once); a
    cell's own HBox/VBox layout must still be the same on the web.
  - Acoustics: the x-t plane figure of "The Riemann problem" is 250 px wide instead of 350 px,
    so its letters are about the size of the text.
  - Comparisons of Riemann solutions (`riemann_tools.make_plot_function` with names, e.g.
    `compare_solutions` in Shallow_water_approximate and Euler_approximate): the legend is
    outside the plots (right of the last one, or of the top one in the vertical layout)
    instead of `loc='best'`, so it no longer jumps as the time changes.
  - Burgers_approximate: the frame slider draws on a live figure (axes drawn once, the curves,
    titles and time lines moved): 16 ms per frame instead of 0.2–0.4 s natively
    (`widgets/figures/burgers_approximate.frames`; tests in `tests/widgets/`).
  - FV_compare (code, user's request): the four `plot_frame` cells draw one legend, right of
    the top plot, instead of one per plot with `loc='best'` (they jumped as the frame changed);
    the same in `widgets/figures/fv_compare.py`.

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
  Parts III–VI of `Index2.ipynb` (one or a few chapters each) are one section, *Further
  topics*, in the same order; `index.md` says so.
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
  - **Part II:** Approximate_solvers, Burgers_approximate, Shallow_water_approximate,
    Euler_approximate, FV_compare. Besides the conventions below:
    - Burgers_approximate, FV_compare (code, approved): `from clawpack import pyclaw,
      riemann` and the `clawpack.riemann...constants` imports became `miniclaw` (as in the
      modules); nothing else changes, and miniclaw reproduces these runs exactly
      (`test_miniclaw_*.py`).
    - Shallow_water_approximate: the citation key `roe1981approximate`, missing from the
      bibliography, is `Roe1981` (the same paper); the cell whose Roe solution has a negative
      middle depth is tagged `remove-stderr`, so its `sqrt` warning (hidden in the original by
      the warning filter removed from `shallow_water.py`) is not shown on the web.
      Bug fix in the chapter's `shallow_water_roe_with_efix` (code, approved): the transonic
      2-wave branch used an undefined `alpha2` (its line was commented out) and the misspelled
      speed `lambda_2_`; now it runs and mirrors the 1-wave fix (`test_approximate_solvers.py`).
    - Euler_approximate: its equation label `SWA:hll_middle_state` (a copy of
      Shallow_water_approximate's) is `EA:hll_middle_state`, since labels are global in the web
      book.
      Bug fix in its `compare_solutions` (code, approved): it read the global `right` instead of
      its argument `right_state` (same values in every call of the chapter, so no output changes).
  - What the conversion does is described in `.agents/conversion.md`:
    - equation references become `{eq}`;
    - citations become `[@key]`;
    - unnumbered displays are kept unnumbered;
    - an `align` with several `\label`s becomes one `align` per label (MyST gives a math block
      one label and one number; in Shallow_water the second labels were lost; approved);
    - a one-row `align` (at most one `&`) becomes an `equation`, and a one-row `align*` plain
      display math: same look and numbers, but a long one can now break after an `=` on narrow
      screens instead of scrolling (approved);
    - `Image` cells become `{image}`;
    - the phase-plane `IFrame` becomes embedded HTML (and `HTML` is added to the cell's
      `IPython.display` import, approved); the acoustics phase plane is the drag explorer on the web
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
  - display equations that cannot wrap and are wider than a phone (Shallow_water_approximate:
    two equations side by side; Euler_approximate: two long aligned rows) are wrapped in a
    `{div}` with class `math-fit` (markup; the LaTeX is unchanged) and shrink to the column.
- Interactive figures on the web (`widgets/`, new): the book's own Python runs in the reader's
  browser (Pyodide, in one worker per page, `widgets/python.mjs`), installed from the wheel that
  `myst.yml` publishes with the site (`static_files`). Before Python is ready the build-time figure
  is shown; without JavaScript it stays. Tests of the interactive figures are in `tests/widgets/`; the Python side: `test_widgets_compute.py`.
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
    is described (controls, rows) in `widgets/figures/`, one module per topic: `advection.py`,
    `burgers.py`, `traffic.py`, `nonconvex.py` (with the chapter's fluxes, named),
    `shallow_water.py`, `euler.py`; a few small functions there give the plotting function a
    cell builds (e.g. `euler.riemann_solution_plot`). Acoustics' figures stay in
    `acoustics_demos.py`, whose notebook functions draw through them (`widgets/figures/acoustics.py`
    imports them). The book's `exact_solvers/*_demos.py` keep only their notebook code. Notebook code
    is unchanged. Test: `test_interactive_cells.py` runs each chapter and checks that every web
    figure has the cell's controls, values and fixed arguments, laid out as in the notebook
    (one per line, or the function's own HBox/VBox layout), and draws the same picture.
  - Part II: the interactive cells of Burgers_approximate, Shallow_water_approximate,
    Euler_approximate and FV_compare (22 figures). The chapters define their solvers and set-ups
    in code cells; their web figures use copies of them, verbatim, in `widgets/figures/`
    (`burgers_approximate.py`, `shallow_water_approximate.py`,
    `euler_approximate.py`, `fv_compare.py`, where each FV_compare set-up imports
    its own constants). The finite-volume runs (miniclaw) are made in the browser when the
    figure first goes live; FV_compare's blast wave with its fine 4000-cell reference takes
    about 10 s natively. Sliders can be integer (`slider(..., integer=True)`, ipywidgets'
    IntSlider). Same test.
  - Fixes after review:
    - Each figure draws on a figure of its own. Some plotting functions draw on pyplot's
      current figure, which could be another figure of the page, so a figure could change its
      number of panels when its slider moved.
    - The controls follow the notebook's layout and widget kinds (radio buttons in
      Shallow_water's comparison of integral curves and Hugoniot loci), styled like ipywidgets:
      the same width for every control, checkboxes under the controls, labels not cut.
    - Figures are shown at 80% of their pixel size (wide, short ones at 95%), at most 60% of
      the window high. The figures output by code cells are shown at 80% too (`book.css`).
    - The "Computed in your browser" line only shows while Python loads (or if it fails), so it
      no longer appears twice when a cell has two figures (`plot_riemann_SW`).
    - Controls redesigned (`interact.css`): one accent colour (the blue of the book's states,
      `--book-accent` in `book.css`, lighter on the dark theme), sliders filled up to their
      value, symbols in the math font. A time slider alone in its row spans the width;
      checkboxes sit in one line; other controls the notebook shows one per line sit side by
      side when there is room (the rows a function lays out itself are kept).
    - When a figure cannot be drawn for some values (e.g. the Euler solver does not converge),
      the figure says so instead of keeping the previous picture; values chosen meanwhile are
      still drawn (`latestOnly` in `python.mjs`).
    - `acoustics_explorer.css` is now `phase_plane_explorer.css`, shared by both drag explorers.
  - `RedrawFigure` draws each frame once, straight to pixels, cropped as Jupyter crops it
    (`savefig(bbox_inches='tight')`) but with a crop that only grows, so the figure no longer
    jumps a few pixels when a tick label widens. The crop is measured again only when the axes
    or titles change. Before, each frame was saved as a PNG (with a tight-bbox pass) and
    decoded again. Test: `test_redraw_figure.py`.
  - `shallow_water_explorer.mjs` (new): drag q_l, q_r in the h-hu plane and the time in the
    x-t plane (Hugoniot loci and integral curves, middle state, waves, depth and momentum at t;
    `exact_solvers.shallow_water` solution). It replaces the mpld3 shallow-water figure on the
    web in Introduction and Shallow_water (that cell is tagged `remove-cell`, approved; the
    file stays for Jupyter). Test: `test_shallow_water_explorer_is_the_exact_solution`.
  - In the browser, modules that import ipywidgets or IPython (notebook only) get empty
    stand-ins, and a missing package (scipy for some chapters) is loaded when first needed.
  - `widgets/assets.py` prepares what the widgets load, in `_build/assets`: the wheel of the
    book's code, Pyodide 0.28.3 with only the packages used (numpy, matplotlib, scipy,
    micropip and their dependencies; checksums verified) and D3 7.9.0. They are hosted with the
    book (about 40 MB), so it does not depend on an outside service.
  - Pyodide is loaded from the jsDelivr CDN, which is much faster than GitHub Pages for large
    files, and from the book's own copy if the CDN fails. Package downloads cut short are
    retried.
  - Python starts as soon as a page with interactive figures opens and imports matplotlib in
    the background (`compute.warm_up`; `test_widgets_compute.py`), so most of its start-up
    (about 9 s) passes while the reader reads; a figure draws when the reader gets near it.
    The static site loads each chapter as a new page, so each chapter starts its own Python.
  - `python.mjs` and the wheel have fixed names, so the widgets load them in a way that never
    uses an old cached copy (otherwise a new widget could meet an old `python.mjs`).
- Figures `shallow_water_riemann` and `nonlinear_elasticity_riemann` (structure of the Riemann
  solution) redrawn as SVG from LaTeX/TikZ sources (`figures/src/`, `sh figures/src/build.sh`):
  the same waves and states, set in Computer Modern at the size of the book's math instead of a
  large sans-serif. The chapters link the `.svg` (Shallow_water, Nonlinear_elasticity); the PNGs
  are removed. In Nonlinear_elasticity the states are written ϵ, as in the chapter's text.
- CI (`.github/workflows/book.yml`): on every push and pull request, runs the tests, prepares
  the widget files and builds the book with `--execute`; pushes to `main` are published on
  GitHub Pages.
- `.agents/tools/`: the conversion script, a prose check and a browser check for horizontal scroll
  bars. These are for the editors; they are not part of the book. The browser check emulates phone widths below 500px
  with a frame of that width (Firefox windows cannot be narrower than 500px, so "390px" used to
  measure 488px). With `--live` it first makes every interactive figure live.
- Not carried over: `make_html.py`, `make_pdf.py`, `make_html_bib.sh`, the Docker files, `html/`,
  `files_for_*`, `html_animations/`, `Index.ipynb`, `Index2.ipynb`, `Make_html_animations.ipynb`.
