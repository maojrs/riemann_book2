# Changes with respect to the original book

Every change compared with the original
[clawpack/riemann_book](https://github.com/clawpack/riemann_book), branch `master`, commit
`5b171f1` (30 Nov 2025). The `FA16` branch is the SIAM print version (2020). Changes to
`exact_solvers/` were approved by the authors.

## Text changes

New text is marked **draft**: it awaits the authors' approval.

- **Home page** (`index.md`, new; **draft**), replacing `Index.ipynb` and `Index2.ipynb`, whose
  chapter lists are now the book's navigation: what the book is, the SIAM edition (its title
  links to the book), "About this web edition" with its subsection "How to use this book" (the
  interactive figures; running the notebooks on Binder or locally), and the license.
  Test: `test_how_to_use_is_on_the_home_page`.
- **Preface** (`chapters/Preface.md`, a markdown page now: it has no code): a new first section,
  "Note on this Web Edition" (**draft**), with a tip linking to "How to use this book", then
  the original preface, word for word. Its citations, raw HTML linking to a missing
  `riemann.html`, are MyST citations (same works).
- **Approximate_solvers:** the title "Part II.  Approximate Riemann Solvers" is "Approximate
  Riemann Solvers" (user's request): the part is already named in the table of contents.
- **References** (user's request):
  - every work links to itself: a DOI for 30 works (from Crossref, checked against title,
    authors and year); otherwise a stable page (Godunov 1959: MathNet; Riemann 1860: EuDML;
    Kröner: Wiley; Garavello & Piccoli, Trangenstein: WorldCat; LeVeque 2002: the author's page,
    as in the original). A citation links to the work, and in a reference list the whole
    reference is the link;
  - new page `chapters/references.md` (**draft**), after *Further topics*: every work of
    `chapters/references.bib` (the cited works and Zobeyer et al. 2013), alphabetical, made by
    `.agents/tools/references_page.py`. Its DOIs go through `hdl.handle.net`, because MyST
    turns doi.org links into citations;
  - bibliography: the duplicate `godunov` is merged into `godunov1959difference`; `Del Razo,
    M. J.` is written so, not shown as "Razo, M. J. D."; Shallow_water_approximate's missing
    key `roe1981approximate` is `Roe1981` (the same paper).

  Tests: `test_every_reference_links_to_the_work`, `test_references_page_lists_every_work`.

## Bug fixes

These don't change any of the book's results.

In `exact_solvers/`:

- `nonlinear_elasticity.py`: 1-shocks had a positive speed and the 1-Hugoniot locus the wrong
  sign, so the 1-wave went right and `fsolve` often failed. Now s = −√([σ]/(ρ[ε])) and
  u* = u_l + √([σ][ε]/ρ). Test: `test_nonlinear_elasticity.py`.
- `traffic_variable_speed.py`: with equal fluxes and q_l > 1/2 > q_r it returned a stationary
  expansion shock instead of the transonic rarefaction.
  Test: `test_equal_speed_limits_reduce_to_LWR`.
- `euler.py`: variable conversions ignored `gamma` and used 1.4. Test: `test_other_gamma`.
- `euler.py`: strong collisions of a heavy, low-pressure gas (in `euler_demo1`'s ranges) made
  `fsolve` fail and return a wrong middle state. When both attempts fail and φ(0) > 0, the
  middle pressure is found by Brent's method on a bracket (φ decreases with p): 220 of the 254
  failures on a 32,400-point grid now solve, the rest are near vacuum and still warn; solutions
  that converged before are unchanged. Test: `test_strong_collisions`.
- `euler_tammann.py`: `primitive_to_conservative` used −γp∞ where the energy needs +γp∞.
  Test: `test_primitive_conservative_round_trip`.
- `nonconvex.py`: `nonconvex_solutions` crashed without explicit `xi_left`/`xi_right`.
  Test: `test_nonconvex_solutions_with_default_xi_range`.
- `acoustics_heterogeneous_demos.interactive_phase_plane`: its $p_{min}$/$p_{max}$ boxes set
  widgets that do not exist there (copied from the Euler version) and raised a `NameError`;
  they set the pressure sliders now.
- `euler_demos.plot_with_stripes`: at t = 0 the pressure was not that of the initial states
  (the energy row was never set, the momentum row twice).
  Test: `test_euler_stripes_at_time_zero_are_the_initial_states`.

In the chapters' code (approved):

- Shallow_water_approximate, `shallow_water_roe_with_efix`: the transonic 2-wave branch used an
  undefined `alpha2` and a misspelled `lambda_2_`; it now mirrors the 1-wave fix.
  Test: `test_approximate_solvers.py`.
- Euler_Tammann, `compare_solutions`: it read the global `right` instead of its argument
  `right_state` (the same values in every call of the chapter).

## Compatibility fixes

These make the code run on current Python, NumPy, Matplotlib and IPython; results unchanged.

- `euler.py`, `shallow_water.py`, `euler_tammann.py`, `interactive_pplanes.py`: the scalar root
  is taken from `fsolve`'s 1-element array (NumPy ≥ 2.4 rejects it); `riemann_tools.
  plot_characteristics` squeezes 1-element speeds (`traffic_LWR.c`). Test: `test_riemann_tools.py`.
- `nonlinear_elasticity.py`, `interactive_pplanes.py`: LaTeX strings are raw (`r'$\gamma$'`).
- `utils/__init__.py` no longer imports `nbtools` (fails on IPython 9); `riemann_tools` lost its
  `__future__`, `six` and JSAnimation imports.
- Nonlinear_elasticity and Pressureless_flow asked for a Python 2 kernel; they name `python3`.
- Seaborn is not used (user's request; Matplotlib 3.6 removed the `seaborn-talk` style):
  Acoustics_heterogeneous no longer calls `sns.set_style('white')`, Pressureless_flow and
  Kitchen_sink_problem no longer call `plt.style.use('seaborn-talk')`.

## Code changes

- **PyClaw → miniclaw.** `from clawpack import pyclaw, riemann` (and the `clawpack.riemann`
  constants) became `from miniclaw import ...` in `acoustics_demos.py`, `burgers_demos.py`,
  `shallow_water.macro_riemann_plot` and the chapters Burgers_approximate, FV_compare,
  Traffic_variable_speed, Nonlinear_elasticity, Traffic_with_ramps and Kitchen_sink_problem
  (approved); Kitchen_sink_problem's `ianimate` comes from `miniclaw.visclaw`. miniclaw
  reproduces these runs (`test_miniclaw_*.py`).
- **`utils` trimmed.** `import utils` no longer loads its submodules (the notebooks use
  `from utils import riemann_tools`). Removed, unused or broken: the modules `animation_tools`,
  `jsanimate_widgets`, `snapshot_widgets`, `nbtools`, `fix_eqref`, `fix_nblinks`, `change_ql`;
  the `riemann_tools` functions `set_interact`, `plot_phase`, `plot_phase_3d`,
  `JSAnimate_plot_riemann`, `waves_from_smoothness` and the Clawpack doctest.
- **`riemann_tools`.** Matplotlib is imported only by the plotting functions, IPython only by
  `riemann_solution(verbose=True)`, so a solution can be computed without them
  (`test_computing_a_solution_does_not_load_matplotlib`). New `sample_riemann` (the sampling of
  `plot_riemann`, split out); `plot_riemann` takes an optional `fig`.
- **Characteristics** (`plot_characteristics`): the speed function is called once per time
  step for all characteristics (5–12 times faster; point by point for functions that only take
  one point), and the lines are drawn as one `LineCollection`. With `extra_lines`
  (Traffic_variable_speed's speed-limit jump) only the characteristics that leave the line on
  their own side, and are not rays of a fan, are drawn: they were drawn twice, as smudged bands
  and a black stripe along x = 0. Tests: `test_vectorized_characteristics_match_the_point_by_point_loop`,
  `test_extra_lines_match_the_point_by_point_loop`.
- `shallow_water.py` no longer silences all warnings on import (approved): the one expected
  warning (u = hu/h in dry regions) is silenced where it occurs; Shallow_water_approximate's
  cell with a negative Roe depth hides its `sqrt` warning (`remove-stderr`).
- Other warnings hidden with `remove-stderr` (code unchanged): invalid escapes in
  Pressureless_flow and Kitchen_sink_problem, its YouTube `HTML` iframe, and scipy's
  `ODEintWarning` in its jump-location cells.
- `acoustics_demos.py` passed the colour twice (`'-k'` and `color=`); the format is `'-'`.
  `shallow_water.phase_plane_plot` and `nonconvex_demos.plot_waves` draw their legend and labels
  on their own axes, not pyplot's current ones.

## Figures

Changes to how the figures look, in Jupyter and on the web. The science shown is the same.

- **Live figures** (`utils/live_figure.py`, `utils/riemann_figure.py`, new): plotting functions
  with a time slider build the figure once and redraw only what depends on t; the drawing code
  is the original, split into a fixed part and an inner `at_time(t)`. Same names, arguments
  and pictures (at most 0.005% of pixels differ), and in a notebook a slider step takes
  17–100 ms instead of 0.25–0.6 s. Used by `riemann_tools.make_plot_function` (most chapters),
  `acoustics_demos`, `burgers.plot_riemann`, `traffic_LWR`, `traffic_demos`, `nonconvex_demos`,
  `shallow_water`, `euler_demos`. Choosing characteristics shows or hides them without
  rebuilding. Tests: `test_riemann_figure.py`, `test_time_figures.py`, `test_acoustics_demos.py`,
  against the previous code in `tests/reference/*_before.py`.
- **Axes that stay put:** Euler's stripes figure holds every value at all times, and its
  stripes cover the domain; `euler_demo1` keeps its ranges while the solution fits them; the
  shallow-water `compare_curves` has a fixed range (−10 to 10), `plot_riemann_SW` shows velocity
  on ±2.3 (and depth on 0 to 2.5 in its two dry-state examples); legends of compared solutions
  (`make_plot_function` with names, FV_compare's `plot_frame`, approved) are outside the plots.
  Tests: `test_euler_stripes_*`, `test_euler_demo_axes_do_not_follow_small_changes`.
- **Labels:** Euler's checkboxes read "1-wave curves"/"3-wave curves" and "Plot 1-loci"/"Plot
  3-loci", as in Shallow_water; Nonconvex_scalar's "Yet another example" sliders read $q_l$
  and $q_r$ (approved).
- **Sizes** (user's request): Acoustics' x-t plane is 250 px wide; Traffic_variable_speed's
  single plots are 6 x 3 inches at the default text size; Pressureless_flow's `connect_states`
  is 8 x 4 inches; Kitchen_sink_problem's profiles have axis labels and sizes like the rest of
  the book, and its animations are 6.4 x 4.8 inches, play smoothly (100 frames, 60 ms each) and
  show the time with two decimals.
- Pressureless_flow: the depth is a black line, not filled blue, as in the rest of the book.
- `shallow_water_riemann` and `nonlinear_elasticity_riemann` are redrawn as SVG from TikZ
  (`figures/src/`): the same diagrams, in the book's math font (ϵ in Nonlinear_elasticity, as in
  its text). The phase-plane HTML files scale to the page width.

## Interactive figures on the web

All 118 interactive figures of the book work on the web, computed by the book's own Python in
the reader's browser (`widgets/`, new). Notebook code is unchanged.

- **Python in the browser:** Pyodide in a worker per page (`python.mjs`), from the jsDelivr CDN
  or the book's own copy; the book's code as a wheel; prepared by `widgets/assets.py`. Python
  starts when the page opens; until it is ready each figure shows its build-time picture.
  Notebook-only modules (ipywidgets, IPython) get stand-ins.
- **The figures:** each interactive cell is described in `widgets/figures/` (one module per
  chapter): the cell's plotting function, its controls and layout. Part II's solvers and
  set-ups are verbatim copies of the chapters' cells. Test: `test_interactive_cells.py` checks
  each web figure against its notebook cell (controls, values, layout, picture).
- **Drag explorers** replace the mpld3 figures (kept for Jupyter): the acoustics phase plane
  (Introduction, Acoustics) and the shallow-water phase plane with the x-t plane (Introduction,
  Shallow_water); the mpld3 cells are tagged `remove-cell` (approved).
  Test: `test_shallow_water_explorer_is_the_exact_solution`.
- **Speed:** time sliders move live figures; figures that are drawn again in full reuse their
  figure and axes (`RedrawFigure`, `KeptAxesFigure`, `KeptAxes`) and measure their crop only when
  their layout changes. Tests: `test_redraw_figure.py`, `test_kept_axes_draw_as_new_axes`,
  `test_pressureless_figure_keeps_its_axes_and_draws_the_chapters_pictures`.
- **Controls** (`interact.mjs`, `interact.css`): the notebook's widgets and layout, styled like
  ipywidgets with the book's accent colour; a lone time slider spans the width, checkboxes sit in
  one line. A figure that cannot be drawn for the chosen values says so.

## Project infrastructure

- **Jupyter Book 2:** `myst.yml` holds the table of contents of `Index.ipynb`/`Index2.ipynb`;
  Parts III–VI are one section, *Further topics* (Part VI's two external notebooks left out).
  The notebooks are in `chapters/` without outputs, figures in `figures/`, `riemann.bib` is
  `chapters/references.bib`; the licenses are copied unchanged.
- **Conversion to MyST** (markup only; a word-level check confirms the prose is unchanged;
  `.agents/conversion.md`): equation references become `{eq}`, citations `[@key]`, `Image`
  cells `{image}`, the phase-plane `IFrame` embedded HTML (`HTML` added to the cell's import,
  approved); links to headings use labels;
  paths are relative to `chapters/`; magics and repeated imports are removed. An `align` with
  several labels becomes one per label (MyST numbers a block once), and one-row `align`s become
  `equation`s (approved). Euler_approximate's label `SWA:hll_middle_state` is
  `EA:hll_middle_state` (labels are global).
- **`book.css`:** a wider text column on large screens, and no horizontal scroll bars at any
  width: equations shrink or break (the few that cannot are wrapped in a `math-fit` div,
  markup only), code wraps, figures, animations and videos fit the column. Figures are shown at
  80% of their pixel size.
- **Binder:** each chapter's rocket icon (top right) opens its notebook on mybinder.org, from the
  `notebooks` branch; Binder installs `pyproject.toml` on Python 3.10, so `requires-python` is
  `>=3.10`.
- **Notebooks download** (`.github/workflows/release.yml`): each published release writes the
  chapters as plain Jupyter notebooks, with only the code they need
  (`.agents/tools/clean_notebooks.py`), to the `notebooks` branch and to
  `riemann_book_notebooks.zip`. Only markdown changes: no web cells; plain Jupyter math with the
  web book's equation numbers, linked citations and headings. Test: `test_clean_notebooks.py`.
- **CI** (`.github/workflows/book.yml`): tests, then builds the book with `--execute`; pushes to
  `main` are published on GitHub Pages.
- **Tests** (`tests/`, pytest, not deployed): the science of `exact_solvers`, `utils` and
  `miniclaw`, and the interactive figures (`tests/widgets/`). `tests/reference/` holds results of
  the book's runs with Clawpack 5.14 (`generate_reference.py`).
- **miniclaw** (`miniclaw/`, new): a pure-Python version of the PyClaw features the book uses
  (classic and SharpClaw solvers, its Riemann solvers, a 1D `ianimate`), with PyClaw's names.
  It reproduces the book's runs exactly. Its `shallow_roe_tracer_1D` splits the tracer wave by
  its speed's sign, where Clawpack's Fortran uses a stale index (no chapter uses it).
- `pyproject.toml` makes the code installable; `README.md` and `.gitattributes` (generated
  and documentation files left out of GitHub's language statistics) are new; `.agents/tools/`
  has the editors' scripts (conversion, prose check, scroll-bar check).
- **Not carried over:** `make_html.py`, `make_pdf.py`, `make_html_bib.sh`, the Docker files,
  `html/`, `files_for_*`, `html_animations/`, `Index.ipynb`, `Index2.ipynb`,
  `Make_html_animations.ipynb`.
