# Plan: architecture, phases and status

## Architecture decisions
- **Framework:** Jupyter Book 2 (mystmd) builds a static site, deployed to GitHub Pages. The notebooks (`.ipynb`) remain the source.
- **Pure Python only:** no Clawpack and no Fortran.
  - The exact solvers stay numpy/scipy.
  - PyClaw is replaced by `miniclaw`, a small, vectorized 1D finite-volume solver: wave propagation, limiters, boundary conditions and approximate Riemann solvers.
- **Interactivity, option C:** interactive figures embedded in the pages with MyST's `{anywidget}` directive (anywidget module format). One in-browser Python worker per page (Pyodide) runs the book's own Python code. Three levels:
  - **Generic slider figure** for every ipywidgets `interact` cell: the book's matplotlib figure, redrawn by Python in the browser. Figures that need speed get a *live* version (`LiveFigure`: built once, only the changing artists are redrawn, raw pixels painted on a canvas), else the whole figure is redrawn (slower, works for any plotting function).
  - **JavaScript figures** only where dragging matters (phase-plane explorers): Python computes the data, JS (D3) draws it.
  - Until Python is ready, the build-time figure is shown; without JavaScript it simply stays.
  - Making the widgets also run in plain Jupyter is optional and later.
- **No Binder** and no live "run cell" layer. JupyterLite (`jupyter: lite: true`) was tried on Acoustics: it works but is slow (11 s to start, 30–90 s to run a chapter, 0.3–0.9 s per slider step) and its widgets overflow on phones.
- **Static fallback:** the CI executes the notebooks at build time, so every figure is visible without JavaScript and is available for PDF export.

## Phases
1. **Foundation.** Copy `exact_solvers`/`utils` in (solvers verbatim), make them installable, remove every Clawpack import, and write `miniclaw`. Build the test suite.
2. **Content conversion.** Convert the notebooks following `.agents/conversion.md`. Configure `myst.yml` with the table of contents from `Index.ipynb` and a `references.bib` from `riemann.bib`. Set up CI that builds with `--execute` and deploys to Pages.
3. **Interactive figures in Acoustics.** Bring the trial design into the repo (steps below), with tests.
4. **Rollout.** Chapter by chapter, SIAM book chapters (Parts I–II) first and the extras later: the generic slider figure for every `interact` cell (whole-figure redraw first), then live versions or JS explorers where they are worth it.
5. **Polish.** PDF export and an optional download of runnable notebooks (with the `{anywidget}` markdown cells removed, since Jupyter shows them as raw text; the code cells give the same figures with ipywidgets). Before release, send the authors the list in "Text to flag for the authors" and apply only the changes they approve.

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
- Step 2, pilot chapter Acoustics: done.
  - Converted with `.agents/tools/convert_notebook.py`; the prose is unchanged (0 word differences).
  - It executes cleanly, and has no horizontal scroll bars at 390–1920 px.
  - The procedure and conventions are in `.agents/conversion.md`.
- Text to flag to the authors is collected in "Text to flag for the authors" below.
- Next: convert the other chapters one at a time with the same procedure (CI is in place, phase 3 step 4).

### Phase 3: in progress
Trial (Acoustics, in a scratch copy) done and agreed. Measured on a 2017 laptop, cold cache:
- Python start-up about 7 s for the drag explorer and 15 s once matplotlib is needed (download 18 MB: Pyodide 5, numpy 3, matplotlib with fonts and Pillow about 9). Start-up is mostly CPU, so the browser cache saves only about 3 s.
- Live figures: 12–40 ms per update (decompose_q about 100 ms: its legend uses `loc='best'`), 20–45 frames/s while dragging; whole-figure redraw 0.3–0.9 s. The JS drag explorer: about 7 ms per update.
- Live figures are pixel-identical to the original functions saved as Jupyter shows them (tight bounding box), except where overlapping lines are drawn in a different order (at most 0.07% of pixels).

Steps, each agreed before it starts:
1. **Done.** `utils/riemann_tools.py`: vectorized `plot_characteristics` (falls back to the per-point loop for speed functions that only take one point), `sample_riemann` split out of `plot_riemann`, matplotlib imported only in the functions that plot. Tests.
2. **Done.** `utils/live_figure.py` (`LiveFigure`, `InteractiveFigure`), and the plotting functions of `acoustics_demos.py` rewritten on it, so the notebook and the web share one copy. `ipywidgets`/`IPython` imported only inside the `*_interactive()` functions. Each demo module holds its controls (ranges, rows) as data, used by both the notebook sliders and the web. Pixel tests against the original figures.
3. **Done.** The browser side (`widgets/`): shared Pyodide worker, generic slider figure, acoustics drag explorer, `compute.py`; URLs relative to the module, not the site root. Acoustics gets one `{anywidget}` markdown cell after each interactive cell. The mpld3 `figures/phase_plane/*.html` are kept, so the notebook cells that show them keep working in local Jupyter. Browser checks.
3b. **Done.** Notebook sliders use the same fast path as the web (figure built once, blitting, quick PNG): 16–29 ms per step locally instead of 130–430 ms.
   Later, optional: one widget for notebook and web (anywidget in Jupyter, with the kernel instead of Pyodide); first check whether MyST can render a widget from a notebook output, which would also remove the `{anywidget}` markdown cells.
4. **Done.** CI (`.github/workflows/book.yml`): tests, `widgets/assets.py` (wheel, Pyodide subset, D3, hosted with the book), build with `--execute` and `BASE_URL=/<repository>`, deploy to GitHub Pages from `main`. Checked locally in a clean copy, served under `/riemann_book2/`. Not yet run on GitHub: Pages must be set to "GitHub Actions" in the repository settings.

Notes collected so far:
- First build warnings to fix during conversion:
  - image paths (`./figures/...`) are relative to the old layout;
  - the equation label `swa:hll_middle_state` is defined in both Shallow_water_approximate and Euler_approximate;
  - cross-references to headings are missing in Shallow_water and Traffic_variable_speed.
- Headless execution (nbclient) stalls on `interact` cells until the cell timeout. CI needs a per-cell timeout or static rendering for them.
- Unconverted chapters carry a temporary `execute: skip: true` first cell, so `jupyter-book start --execute` only runs converted chapters.
- `seaborn` is imported by Acoustics_heterogeneous, Kitchen_sink_problem and Pressureless_flow but is not a dependency. Decide at conversion: add it (it exists in Pyodide) or replace the styling.
- Nonlinear_elasticity and Pressureless_flow ask for a `python2` kernel; set it to `python3` at conversion (metadata only).
- The removed Matplotlib style `seaborn-talk` is used in Pressureless_flow and Kitchen_sink_problem.
- Warnings in notebook code, previously hidden by a global filter in `shallow_water.py`:
  - Shallow_water_approximate: `np.sqrt` of a negative depth;
  - Pressureless_flow: invalid escape sequences (`'\l'`) in LaTeX strings (use raw strings).
- Kitchen_sink_problem set no `dry_tolerance`/`sea_level`, which Clawpack 5.14 requires. miniclaw does not need them.
- Code in the chapters may be changed only if the change is small and the user approves it first.
- Pyodide and D3 are hosted with the book (step 4). With the CDN, start-up once took 45–95 s (an 8.6 MB file took 49 s); self-hosted, served locally: explorer live in about 6 s, slider figures in 12–17 s.
- MyST copies `static_files` both to the site root (dev server) and to `_public/` (static build), so Pyodide is in the site twice; the site is about 92 MB.
- The theme still loads KaTeX, Font Awesome and a jupyter-matplotlib stylesheet from CDNs; not ours to change for now.
- Interactive-figure trial findings: MyST renders anywidgets in a shadow DOM; thebe-lite's micropip fails to install a wheel from a URL (unzip it instead); the widgets' URLs must not assume the site root (GitHub Pages serves under `/riemann_book2/`); Pyodide's toJs turns None into undefined.
- Keep the table of contents in `myst.yml` explicit, so that `AGENTS.md`, `CHANGES.md` and `.agents/` are not rendered as pages.

## Text to flag for the authors
Original text that refers to things that no longer exist or have changed. Not changed (rule 1); add to this list during conversion, by chapter.
- index.md: the new front page is a draft; its wording needs approval.
- Index (Part II description): FV_compare "when used with PyClaw" (now miniclaw).
- Approximate_solvers: the chapter is itself titled "Part II. Approximate Riemann Solvers".
- Acoustics:
  - the "on github" code links point to `blob/FA16`;
  - "in the notebook version, or on [this webpage](http://www.clawpack.org/riemann_book/phase_plane/...)";
  - "produced using a numerical method from PyClaw … or on [this webpage]" (now miniclaw; old clawpack.org page);
  - "*In the live notebook, you can advance the above solutions in time…*" and similar "In the live notebook…" sentences (the web figures are now live too).

## Open decisions
- None at the moment.
