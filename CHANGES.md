# Changes with respect to the original book

This file records every change made in this edition compared with the original
*Riemann Problems and Jupyter Solutions* repository.

- **Baseline:** [clawpack/riemann_book](https://github.com/clawpack/riemann_book), branch
  `master`, commit `5b171f1` (30 Nov 2025). The `FA16` branch is the version printed by SIAM (2020).
- Every change to the original solver code (`exact_solvers/`) was approved by the authors before
  it was applied.
- Each entry names the test in `tests/` that checks it.

## Text changes

None so far.

## Bug fixes in the solvers

These change results, but only in cases that none of the book's own examples use. The figures and
numbers in the book are unchanged.

1. **Nonlinear elasticity: 1-shocks travelled the wrong way** (`exact_solvers/nonlinear_elasticity.py`).
   - The bug: the 1-shock speed was `+sqrt(...)` and the 1-Hugoniot locus was `u_l - sqrt(...)`.
   - The jump conditions s[ε] = −[u] and s[ρu] = −[σ] give s = −√([σ]/(ρ[ε])) and
     u* = u_l + √([σ][ε]/ρ). The locus is now also tangent to the 1-integral curve, as it must be.
     The fix is in `exact_riemann_solution` and `phase_plane_plot`.
   - Effect: any Riemann problem with a 1-shock gave a right-going 1-wave, and `fsolve` usually
     failed to converge. The chapter's example has only a 1-rarefaction; the interactive widgets
     could reach the bug.
   - Test: `tests/test_nonlinear_elasticity.py`.
2. **Variable speed limit traffic: expansion shock when the fluxes are exactly equal**
   (`exact_solvers/traffic_variable_speed.py`).
   - The bug: if v_l q_l(1−q_l) == v_r q_r(1−q_r) exactly, a stationary jump was returned even when
     q_l > 1/2 > q_r. That jump violates the entropy condition (demand/supply at x = 0); the correct
     solution is the transonic rarefaction.
   - Example: q_l = 0.75, q_r = 0.25, v_l = v_r. Only exact floating-point equality triggers it.
   - Test: `tests/test_traffic_variable_speed.py::test_equal_speed_limits_reduce_to_LWR`.
3. **Euler: `gamma` was ignored in variable conversions** (`exact_solvers/euler.py`).
   - The bug: `exact_riemann_solution`, `cons_to_prim` and `phase_plane_plot` converted between
     primitive and conserved variables with the default γ = 1.4, whatever `gamma` was passed.
     Results were wrong for any other γ.
   - Effect: none on the book, which always solves Riemann problems with γ = 1.4. The γ sliders
     only affect the integral-curve and Hugoniot-locus plots, which were already correct.
   - Test: `tests/test_euler.py::test_other_gamma`.
4. **Euler with the Tammann EOS: sign error in the energy** (`exact_solvers/euler_tammann.py`).
   - The bug: `primitive_to_conservative` used E = (p − γp∞)/(γ−1) + ρu²/2.
     `conservative_to_primitive` (and the stiffened-gas EOS) use E = (p + γp∞)/(γ−1) + ρu²/2.
   - Effect: none on the book, which uses primitive variables only.
   - Test: `tests/test_euler_tammann.py::test_primitive_conservative_round_trip`.
5. **Nonconvex scalar solutions: crash with the default ξ range** (`exact_solvers/nonconvex.py`).
   - The bug: `nonconvex_solutions` used `xi_left`/`xi_right` before setting their default values.
   - Effect: none on the book, which always passes explicit values.
   - Test: `tests/test_nonconvex.py::test_nonconvex_solutions_with_default_xi_range`.

## Compatibility fixes (current Python, NumPy, IPython)

These don't change any results; they only make the code run on current versions.

1. **`fsolve` returns a 1-element array** (`euler.py`, `shallow_water.py`, `euler_tammann.py`,
   `interactive_pplanes.py`).
   - Problem: NumPy ≥ 2.4 no longer stores such an array into an array element, so every Euler,
     shallow-water and Tammann solution crashed.
   - Fix: one added line after each `fsolve` call takes the scalar root, e.g. `p = p[0]`.
   - Tests: `tests/test_euler.py`, `tests/test_shallow_water.py`, `tests/test_euler_tammann.py`.
2. **Invalid escape sequences** in LaTeX strings (`nonlinear_elasticity.py`, `interactive_pplanes.py`).
   - Problem: strings like `'$\gamma$'` give a warning today and will be an error in a future Python.
   - Fix: made them raw strings (`r'$\gamma$'`).
3. **`utils` could not be imported with IPython 9.**
   - Problem: `utils/__init__.py` imported `utils/nbtools.py`, which uses the removed
     `IPython.core.display.display`.
   - Fix: `utils/__init__.py` no longer imports its submodules.
4. **Python 2 leftovers removed from `utils/riemann_tools.py`:** `from __future__ ...`,
   `from six.moves import range`, and an unused optional JSAnimation import.

## Interface changes

Changes to how the code is imported or called.

1. `import utils` no longer loads `utils.nbtools`, `utils.animation_tools` and `utils.riemann_tools`
   automatically. Import them explicitly, e.g. `from utils import riemann_tools`, which is what all
   the notebooks already do.

## Project infrastructure

- `exact_solvers/` and `utils/` are installable with `pyproject.toml` (`uv sync` or
  `pip install -e .`). Notebooks no longer need to run from the repository folder.
- Added a scientific test suite in `tests/` (pytest). It is not part of the deployed book.
- Not carried over from the original repository: the build scripts (`make_html.py`, `make_pdf.py`,
  `make_html_bib.sh`), the Docker files, and the generated `html/` and `files_for_*` folders.
