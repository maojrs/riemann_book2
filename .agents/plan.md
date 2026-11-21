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
- **No Binder inside the pages** and no live "run cell" layer (each chapter's header only links to its notebook on Binder, opened in a new tab: `edit_url` per chapter, launch icon in `book.css`; it opens the `notebooks` branch, which `.github/workflows/release.yml` rewrites on each release with the cleaned notebooks (`.agents/tools/clean_notebooks.py`), also attached to the release as `riemann_book_notebooks.zip`; Binder installs its `pyproject.toml` on Python 3.10; decided 2026-11-21. The GitHub icon still points to clawpack/riemann_book: switch it to this repository at the official release; the download link of `how_to_use.md` and the README badge use this repository's latest release (TODO in `how_to_use.md`), to be set then too). JupyterLite (`jupyter: lite: true`) was tried on Acoustics: it works but is slow (11 s to start, 30–90 s to run a chapter, 0.3–0.9 s per slider step) and its widgets overflow on phones.
- **Static fallback:** the CI executes the notebooks at build time, so every figure is visible without JavaScript and is available for PDF export.

## Phases
1. **Foundation.** Copy `exact_solvers`/`utils` in (solvers verbatim), make them installable, remove every Clawpack import, and write `miniclaw`. Build the test suite.
2. **Content conversion.** Convert the notebooks following `.agents/conversion.md`. Configure `myst.yml` with the table of contents from `Index.ipynb` and a `references.bib` from `riemann.bib`. Set up CI that builds with `--execute` and deploys to Pages.
3. **Interactive figures in Acoustics.** Bring the trial design into the repo (steps below), with tests.
4. **Rollout.** Chapter by chapter, SIAM book chapters (Parts I–II) first and the extras later: the generic slider figure for every `interact` cell (whole-figure redraw first), then live versions or JS explorers where they are worth it.
5. **Polish.** PDF export and a download of runnable notebooks: the README's "Download notebooks" button already points to `releases/latest/download/riemann_book_notebooks.zip`, to be made by the CI on each release (notebooks plus `exact_solvers`, `utils`, `miniclaw` and a minimal requirements file; with the `{anywidget}` markdown cells removed, since Jupyter shows them as raw text; the code cells give the same figures with ipywidgets). Before release, send the authors the list in "Text to flag for the authors" and apply only the changes they approve.

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
- Step 3, Part I converted (2026-11-20, overnight): Introduction, Advection, Burgers, Traffic_flow, Nonconvex_scalar, Shallow_water, Shallow_tracer, Euler. Prose unchanged (0 differences each), all execute cleanly, no horizontal scroll bars at 390 (true phone width, see conversion.md), 768, 1280, 1440, 1920 px. Details of what each needed are in CHANGES.md; text to flag is below.
- Step 2, pilot chapter Acoustics: done.
  - Converted with `.agents/tools/convert_notebook.py`; the prose is unchanged (0 word differences).
  - It executes cleanly, and has no horizontal scroll bars at 390–1920 px.
  - The procedure and conventions are in `.agents/conversion.md`.
- Text to flag to the authors is collected in "Text to flag for the authors" below.
- Next: Parts II–V, one chapter at a time with the same procedure.

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
- seaborn: no longer used (2026-11-20, user): the seaborn styling of three Further topics chapters was removed.
- Nonlinear_elasticity and Pressureless_flow ask for a `python2` kernel; set it to `python3` at conversion (metadata only).
- Warnings in notebook code, previously hidden by a global filter in `shallow_water.py`:
  - Shallow_water_approximate: `np.sqrt` of a negative depth;
  - Pressureless_flow: invalid escape sequences (`'\l'`) in LaTeX strings (use raw strings).
- Kitchen_sink_problem set no `dry_tolerance`/`sea_level`, which Clawpack 5.14 requires. miniclaw does not need them.
- Code in the chapters may be changed only if the change is small and the user approves it first.
- Live site (first deploy): GitHub Pages served large files at about 240 KB/s, so Python took 56 s (explorer) to 110 s (sliders); on an iPhone (Chrome) it failed with "No module named numpy", most likely a download cut short (Pyodide only logs failed packages). Since then: Pyodide from jsDelivr first, the book's copy as fallback; failed package downloads retried 3 times, then a clear error; Python started only when a figure came near (since 2026-11-20 it starts when the page opens, see below). Locally: first figure live 14–17 s after scrolling to it, the next ones about 3 s. On the iPhone Python then loaded, but a cached old `python.mjs` met new widgets ("whenNear is not a function"): fixed by loading `python.mjs?v=<page load time>` and fetching the wheel with `cache: 'no-cache'`.
- Pyodide and D3 are hosted with the book (step 4). With the CDN, start-up once took 45–95 s (an 8.6 MB file took 49 s); self-hosted, served locally: explorer live in about 6 s, slider figures in 12–17 s.
- MyST copies `static_files` both to the site root (dev server) and to `_public/` (static build), so Pyodide is in the site twice; the site is about 92 MB.
- The theme still loads KaTeX, Font Awesome and a jupyter-matplotlib stylesheet from CDNs; not ours to change for now.
- Interactive-figure trial findings: MyST renders anywidgets in a shadow DOM; thebe-lite's micropip fails to install a wheel from a URL (unzip it instead); the widgets' URLs must not assume the site root (GitHub Pages serves under `/riemann_book2/`); Pyodide's toJs turns None into undefined.
- Keep the table of contents in `myst.yml` explicit, so that `AGENTS.md`, `CHANGES.md` and `.agents/` are not rendered as pages.

### Phase 4: Part I done (2026-11-20, overnight)
- All 56 interactive figures of Part I (besides Acoustics) are live on the web as redraw figures (0.2–1 s per change); checked in the browser (every figure live, every control redraws) and with `pagecheck.py --live` at 390–1920 px.
- Shallow-water drag explorer done (`widgets/shallow_water_explorer.mjs`), in Introduction and Shallow_water.
- Review fixes (user's review, 2026-11-20, steps 1–2 agreed): each redraw figure on its own pyplot figure (they drew on each other); controls laid out and styled as in the notebook (tested against the original widgets' order and HBox/VBox layout); figures at 3/4 size, at most 60vh; status line only while loading; `RedrawFigure` draws once straight to pixels with a crop that only grows.
- Step 3 done (2026-11-20): every time-slider figure of Part I draws on a live figure (`utils.live_figure.TimeFigure`), in the notebooks too: `riemann_tools.make_plot_function` (`utils/riemann_figure.py`), `burgers.plot_riemann`, `traffic_LWR.plot_riemann_traffic`, `traffic_demos.jam`/`green_light`, the nonconvex `make_plot_function`s, `shallow_water.make_demo_plot_function` (and `plot_riemann_SW`'s stripes), `euler_demos.plot_with_stripes`. Notebook steps 17–26 ms (80–100 ms with stripes) instead of 245–590 ms. Still redrawn in full (0.1–0.4 s natively): the single-plot figures without a time slider (Hugoniot loci, integral curves, connect_states, Burgers' multivalued/rarefaction figures, Advection's characteristics).
- Part II converted (2026-11-20): Approximate_solvers, Burgers_approximate, Shallow_water_approximate, Euler_approximate, FV_compare; 0 prose differences; 22 live figures (the chapters' own solvers and set-ups copied into `widgets/figures/*_approximate.py`, `widgets/figures/fv_compare.py`). Approved code changes: `clawpack` → `miniclaw` imports in Burgers_approximate and FV_compare; the chapters' bugs below fixed (transonic 2-wave branch of `shallow_water_roe_with_efix`, `right` in Euler_approximate's `compare_solutions`).
- Controls redesigned (frontend-design): time slider full width, checkboxes in one line, same-kind one-per-line controls side by side, accent `--book-accent`. Tests of the interactive figures are in `tests/widgets/`.
- Euler exact solver fixed (approved, 2026-11-20): when both `fsolve` attempts fail and phi(0) > 0, p_m is found by Brent's method on a bracket (220 of 254 failures on a 32,400-point grid of `euler_demo1`'s ranges; 34 near-vacuum cases still warn as before).
- Python start-up (measured 2026-11-20, Firefox, files cached): Pyodide 2.5 s, numpy + micropip + the book's wheel + `compute` 2 s, matplotlib package 1 s, `import matplotlib` 1.1 s, `import matplotlib.pyplot` 2–2.6 s (not the font cache: it stays empty), first figure 0.5 s; about 9.5 s in all, mostly CPU. MyST's static build sets `reloadDocument` on every link, so each chapter is a new page load and Python cannot be kept between chapters. Done: Python starts when the page opens and imports pyplot in the background (`compute.warm_up`); first figure live 0–5 s after scrolling to it if the reader scrolls after 5–10 s (Euler: scipy adds about 3 s), instead of about 10–13 s. Possible later: Pyodide memory snapshots (experimental; restore in about 1–2 s, snapshot tens of MB, cached in the browser).
- Table of contents (user, 2026-11-20): Parts III–VI of the original are one section, *Further topics* (unnumbered: not in the print book).
- Web figure definitions moved to `widgets/figures/` (user, 2026-11-20): one module per topic; `exact_solvers/` keeps only the book's modules (the `*_demos.py` with their notebook code). Acoustics' figures stay in `acoustics_demos.py` (its notebook functions use them), imported by `widgets/figures/acoustics.py`.
- Further topics converted (2026-11-20): Acoustics_heterogeneous, Traffic_variable_speed, Nonlinear_elasticity, Euler_Tammann, Traffic_with_ramps, Pressureless_flow, Kitchen_sink_problem; 0 prose differences (Euler_Tammann: only the markup of two bare `\ref`s); 35 live figures. Approved code changes: `clawpack` → `miniclaw` imports (Traffic_variable_speed, Nonlinear_elasticity, Traffic_with_ramps, Kitchen_sink_problem, with `miniclaw.visclaw.ianimate`); no seaborn styling (user, so the plots look like Parts I–II; Pressureless_flow's connect_states 8 x 4 like Shallow_water's). The converter left one-row `align*` blocks with nested environments without delimiters (fixed in `convert_notebook.py`; earlier chapters had none). Figure-format fixes (user, 2026-11-21): Traffic_variable_speed default 6 x 3 figures at matplotlib's 10-point text; Pressureless_flow depth not filled; Kitchen_sink_problem figure sizes, axis labels and 6.4 x 4.8 animations (100 frames, 60 ms, centred). `extra_lines` characteristics only where they leave the line and are not fan rays (no duplicates, no stripe on x = 0). Kept axes (`KeptAxesFigure`) for the "all in one" figures of Traffic_variable_speed and Traffic_with_ramps and Pressureless_flow's connect_states: Traffic_with_ramps 0.55–0.9 s per change in Firefox (was about 1.2 s), connect_states 0.4–0.47 s (was 0.57 s). Pressureless_flow's g slider keeps its axes too (`TimeFigure(axes=...)`, crop measured once per layout): about 250 ms natively for a new g (was 410), 125 ms for one seen before. The rest of each change is matplotlib drawing text and lines, and computing characteristics and car paths.

### Phase 4 decisions (user, 2026-11-20)
- Interactive cells that call `interact(...)` in the notebook: each gets an `InteractiveFigure` in its demo module (the cell's sliders written as data) and an `{anywidget}` markdown cell after the code cell; notebook code unchanged. Fluxes defined as lambdas in a notebook get a small named function in the demo module that builds the same flux.
- Speed: whole-figure redraw first for every interactive cell (an `InteractiveFigure` can wrap a plain plotting function), `LiveFigure` versions later for the most used ones.
- A shallow-water drag explorer (like the acoustics one) to replace the mpld3 figure: after the slider figures, if time allows.

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
- Every Part I chapter: the "on github" code links point to `blob/FA16`.
- Introduction: "*(as an animation in the live notebook or html versions)*"; "Below (in the notebook version, or on [this webpage](http://www.clawpack.org/riemann_book/phase_plane/acoustics_small.html))"; "Below, in the notebook, or on [this webpage](…/shallow_water_small.html), we provide an interactive view…".
- Advection: "*In the live notebook, you can adjust the advection speed a…*"; "*In the live notebook you can advance a time slider…*".
- Burgers: "In the live notebook, the figure below shows possible locations for the shock…"; "…in the interactive solution below (in the notebook)"; "In the live notebook, the figure below is an interactive solution…"; "computed numerically using [PyClaw]" (now miniclaw); four animations "in the notebook, or on [this webpage](…/burgers_animation0–3.html)".
- Traffic_flow: "In the live notebook, the interactive module below shows … with slider bars to adjust these."
- Nonconvex_scalar: "In the live notebook you can see how the solution evolves with time."; "Here's another example that you can run in a live notebook."
- Shallow_water: three "*In the interactive notebook you can …*" sentences (one with the typo "charactersitics"); "The live notebook, or [this webpage](…/shallow_water_small.html), provides an interactive view…".
- Shallow_tracer: "*In the live notebook you can select which set of characteristics to plot."
- Euler: "*In the live notebook, you can easily adjust the initial data and immediately see the resulting solution.*"
- Approximate_solvers: "implemented in Clawpack" (the wave propagation algorithms; still true of Clawpack, the book now uses miniclaw).
- Burgers_approximate: "numerical solutions obtained with PyClaw", "as seen in the PyClaw example above", "We now repeat the PyClaw simulation" (now miniclaw); two "*In the live notebook you can try adjusting $N$…*"; link to `blob/FA16/exact_solvers/burgers.py`.
- Shallow_water_approximate, Euler_approximate: "An implementation of this solver for use in Clawpack can be found [here](…/riemann/blob/FA16/src/…)"; links to `blob/FA16/exact_solvers/…`. Fixed with approval (2026-11-20), for the authors to know: the transonic 2-wave branch of `shallow_water_roe_with_efix` (undefined `alpha2`, misspelled `lambda_2_`) and `right` → `right_state` in Euler_approximate's `compare_solutions`.
- Euler_approximate, Shallow_water_approximate: both defined the equation label `SWA:hll_middle_state`; labels are global in the web book, so Euler_approximate's is now `EA:hll_middle_state` (markup).
- FV_compare: the introduction on PyClaw ("we will use them within PyClaw", "templates for setting up other problems in PyClaw", "approximate Riemann solvers from PyClaw that can be found in these files" with `blob/FA16` links); "implemented in PyClaw"; two "in the live notebook" sentences (increase N, refine the grid).
- Traffic_variable_speed: "*In the live notebook, you can continue to experiment with this system using the interactive setup below*" (the web figure is live too).
- Kitchen_sink_problem: "we set up a finite volume simulation using PyClaw" (now miniclaw).
- Further topics in general: the seaborn styling of Acoustics_heterogeneous, Pressureless_flow and Kitchen_sink_problem was removed (code, user's request); Part VI's two external nbviewer notebooks (multidimensional acoustics and elasticity) are still left out.

## Open decisions
- None at the moment.
