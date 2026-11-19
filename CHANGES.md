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

## Project infrastructure

- `pyproject.toml` makes `exact_solvers` and `utils` installable (`uv sync` or `pip install -e .`).
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
  - **Acoustics.**
  - What the conversion does is described in `.agents/conversion.md`:
    - equation references become `{eq}`;
    - citations become `[@key]`;
    - unnumbered displays are kept unnumbered;
    - `Image` cells become `{image}`;
    - the phase-plane `IFrame` becomes embedded HTML;
    - paths are made relative to `chapters/`;
    - notebook magics and repeated import cells are removed.
- Chapters not yet converted have a temporary first cell `execute: skip: true`, so the build
  (`--execute`) does not run them. Each is removed when its chapter is converted.
- `figures/phase_plane/*.html`: a short script appended to each file scales the figure to the
  page width.
- `book.css` also prevents horizontal scroll bars:
  - equations fit their box and are centred (the theme sets their margins to 0, which put them on the left);
  - long code lines wrap;
  - the top-bar title shrinks on small screens;
  - ipywidgets placeholders are hidden on the static site.
- `.agents/tools/`: the conversion script, a prose check and a browser check for horizontal scroll
  bars. These are for the editors; they are not part of the book.
- Not carried over: `make_html.py`, `make_pdf.py`, `make_html_bib.sh`, the Docker files, `html/`,
  `files_for_*`, `html_animations/`, `Index.ipynb`, `Index2.ipynb`, `Make_html_animations.ipynb`.
