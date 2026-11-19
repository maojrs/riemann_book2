# Plan: architecture, phases and status

## Architecture decisions
- **Framework:** Jupyter Book 2 (mystmd) builds a static site, deployed to GitHub Pages. The notebooks (`.ipynb`) remain the source.
- **Pure Python only:** no Clawpack and no Fortran.
  - The exact solvers stay numpy/scipy.
  - PyClaw is replaced by `miniclaw`, a small, vectorized 1D finite-volume solver: wave propagation, limiters, boundary conditions and approximate Riemann solvers.
- **Interactivity, option C:** a few reusable interactive components embedded in the pages, for example a Riemann-solution explorer, a phase plane, a time animation and a solver comparison.
  - Each component sends its parameters to a shared in-browser Python worker (Pyodide) that runs the book's Python solvers. JS draws the results.
  - Prefer anywidget, so the same components also work in plain Jupyter.
- **No Binder** and no live "run cell" layer: it is too slow and not worth the experience cost.
- **Static fallback:** the CI executes the notebooks at build time, so every figure is visible without JavaScript and is available for PDF export.

## Phases
1. **Foundation.** Copy `exact_solvers`/`utils` in (solvers verbatim), make them installable, remove every Clawpack import, and write `miniclaw`. Build the test suite.
2. **Content conversion.** Convert the notebooks following `.agents/conversion.md`. Configure `myst.yml` with the table of contents from `Index.ipynb` and a `references.bib` from `riemann.bib`. Set up CI that builds with `--execute` and deploys to Pages.
3. **Component prototype.** Build one representative interactive figure end to end (Pyodide worker, JS plot, MyST embedding), done early in parallel with phases 1–2 to reduce risk.
4. **Rollout.** Replace static or ipywidgets figures with components chapter by chapter, SIAM book chapters (Parts I–II) first and the extras later.
5. **Polish.** PDF export and an optional download of runnable notebooks.

## Status

### Phase 1: done
- `exact_solvers/` and `utils/` come from riemann_book master (commit `5b171f1`). They are installable with `pyproject.toml` (`uv sync`).
- The solvers are unchanged except for user-approved fixes, all listed in `CHANGES.md`.
- `utils/` is now only `riemann_tools.py`. It stays there so the notebook imports match the print book.
- `miniclaw/` replaces PyClaw: the classic and SharpClaw solvers and every Riemann solver the book uses. It reproduces all the book's PyClaw runs bit for bit; design and implementation notes are in `.agents/miniclaw.md`.
- No Clawpack imports are left.
- 285 tests in `tests/`, checking the science and agreement with the Clawpack reference results in `tests/reference/`.

### Phase 2: in progress
- Step 1, book skeleton: done. `chapters/` (22 notebooks, outputs stripped, sources unchanged), `figures/`, `references.bib`, `myst.yml`, draft front page `index.md`. Builds 23 pages with `uv run jupyter-book build --html`.
- Waiting for the user:
  - approval of the wording of the draft front page `index.md`;
  - Part VI's two external nbviewer notebooks (multidimensional acoustics and elasticity) are left out of the table of contents for now. **Ask the user later** whether to include them.
- Sidebar: tried a flat table of contents with part pages instead of dropdowns; the user preferred the original nested parts (reverted).
- `book.css` widens the text column on screens of 1024px and wider. If the theme changes its grid, regenerate the override from the theme's `.article-grid` rules.
- To flag to the authors: the Part II description of FV_compare says "when used with PyClaw" (now miniclaw), and the Approximate_solvers chapter is itself titled "Part II. Approximate Riemann Solvers".
- Next: convert a pilot chapter (Acoustics, compared with jbook2test) and settle the conversion script.

Notes collected so far:
- First build warnings to fix during conversion:
  - image paths (`./figures/...`) are relative to the old layout;
  - the equation label `swa:hll_middle_state` is defined in both Shallow_water_approximate and Euler_approximate;
  - cross-references to headings are missing in Shallow_water and Traffic_variable_speed.
- Headless execution (nbclient) stalls on `interact` cells until the cell timeout. CI needs a per-cell timeout or static rendering for them.
- The removed Matplotlib style `seaborn-talk` is used in Pressureless_flow and Kitchen_sink_problem.
- Warnings in notebook code, previously hidden by a global filter in `shallow_water.py`:
  - Shallow_water_approximate: `np.sqrt` of a negative depth;
  - Pressureless_flow: invalid escape sequences (`'\l'`) in LaTeX strings (use raw strings).
- Kitchen_sink_problem set no `dry_tolerance`/`sea_level`, which Clawpack 5.14 requires. miniclaw does not need them.
- Keep the table of contents in `myst.yml` explicit, so that `AGENTS.md`, `CHANGES.md` and `.agents/` are not rendered as pages.

## Open decisions
- Whether interactive components use anywidget, so they also run in plain Jupyter, or web-only JS. Leaning towards anywidget.
