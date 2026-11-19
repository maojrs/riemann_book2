# AGENTS.md — Riemann Problems and Jupyter Solutions, 2nd edition (web)

## Project goal
Port the interactive book *Riemann Problems and Jupyter Solutions* (Ketcheson, LeVeque, del Razo; SIAM 2020) to a modern web book that runs entirely in the browser. This is a **second edition**: the content and science stay the same, while the tooling, interactivity and code are modernized.

## Repositories
- Original book, **master** branch (latest; source of truth for text and solvers): https://github.com/clawpack/riemann_book/tree/master
  - The FA16 branch is the version printed by SIAM (2020), for reference only.
- Jupyter Book 2 trial port (Acoustics, Burgers): https://github.com/maojrs/jbook2test
- This repo: the new edition.

## Read when needed
- `.agents/plan.md`: architecture, phases, current status and open decisions. Read it before planning or starting a phase, and update the status when a step is done.
- `.agents/conversion.md`: notebook-to-MyST conventions. Read it before converting a chapter.
- `.agents/miniclaw.md`: miniclaw design and decisions. Read it before working on `miniclaw/`.

## Repository layout
The repo should look like a book, not like complex software.

```
riemann_book2/
├── README.md
├── CHANGES.md        # record of every change vs. the original book
├── myst.yml          # book config + table of contents (defines chapter order)
├── references.bib    # bibliography (from riemann.bib)
├── pyproject.toml    # makes the code folders installable (pip install -e .; Pyodide wheel)
├── chapters/         # all notebooks, book chapters and extras, original names, no numbers
├── figures/          # static images
├── exact_solvers/    # the book's exact solvers, verbatim (+ approved fixes only)
├── utils/            # riemann_tools: compute and plot Riemann solutions (may be rewritten)
├── miniclaw/         # new: minimal educational reimplementation of Clawpack/PyClaw
├── components/       # later: JS/anywidget interactive figures
├── tests/
└── .github/, .agents/   # CI and agent notes (hidden)
```

- Keep the original import names (`from exact_solvers import burgers`, `from utils import riemann_tools`) so notebook code cells stay as in the print book.
- No `src/` folder and no wrapper package. Chapter order lives only in `myst.yml`.
- Do not commit generated output (HTML, animations, build folders) and do not carry over the old build scripts or Docker files.
- `miniclaw` must state that it is a minimal educational reimplementation of the Clawpack algorithms, not Clawpack itself.

## Rules (mandatory)
Work step by step: agree on each step with the user before implementing it, and do not run ahead of the agreed plan.

1. **Never modify the original text of the book.**
   - The only exception: wording that refers to a figure or interactive plot that changed, such as "move the slider" becoming "drag the point".
   - Markup conversion is allowed. The wording must stay identical.
   - **The science must remain the same:** equations, statements, parameters and conclusions.
   - When in doubt, leave the text and flag it for the authors.
2. **Never modify the original scientific code (the exact solvers) without the user's approval.**
   - The numerical code of the original `exact_solvers/` modules is copied **verbatim**.
   - Changes are allowed only to fix bugs, old-Python issues or severe slowdowns, and each one must be proposed, explained and **approved before it is applied**.
   - Code that replaces PyClaw/Clawpack (`miniclaw`) is new code and may be written freely.
   - Plotting, widgets and utilities may be rewritten freely, as long as the figures show the same science.
3. **All Python code must be tested for scientific accuracy.**
   - Every Python function or feature gets a pytest test under `tests/`.
   - Tests check the science: Rankine–Hugoniot and entropy conditions, exact solutions of known Riemann problems, conservation, convergence of finite-volume results to exact solutions, and agreement with the original book's outputs where applicable.
   - Tests are not part of the deployed book. They run in CI, and CI must pass before merging or deploying.
4. **Register every change in `CHANGES.md`.**
   - Every change compared with the original book goes there, in the matching section: text changes, bug fixes in the solvers, compatibility fixes, interface changes, project infrastructure.
   - Keep entries short and simple: one or two lines saying what changed and why, and the test that covers it.
5. **Code must be well organized, simple, concise and human-readable.**
   - Small, focused modules and functions with clear names and short docstrings stating the equations or method.
   - No dead code, no `sys.path` hacks, no Python 2 leftovers (`six`, `__future__`).
   - Prefer clarity over cleverness: this code is read by students.
