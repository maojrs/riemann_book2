# miniclaw design

A minimal, pure-Python, educational reimplementation of the Clawpack/PyClaw
algorithms that the book uses (1D only). It is not Clawpack itself.

## Decisions (agreed with the user)
- **API:** a PyClaw-compatible subset. Same class, attribute and Riemann-solver names, so the
  notebook code cells only change their imports (`from clawpack import pyclaw` becomes
  `from miniclaw import pyclaw, riemann`).
- **SharpClaw:** implement `SharpClawSolver1D` (WENO5 + SSP Runge–Kutta), built last.
- **Reference data:** a script runs the book's PyClaw setups with real Clawpack and saves `.npz`
  files in `tests/reference/`. The tests compare miniclaw against them.

## What the book uses (master branch)
- `ClawSolver1D`: `order` (1 or 2), `limiters` (default minmod; MC in FV_compare),
  `bc_lower`/`bc_upper`, `aux_bc_lower`/`aux_bc_upper`, `all_bcs`, `BC.extrap`/`wall`/`periodic`/`custom`,
  `user_bc_lower`/`user_bc_upper`, `step_source`, `dt_initial`, `num_eqn`. `kernel_language` is accepted and ignored.
- Grid: `Dimension(lower, upper, num_cells, name)` with `.centers`, `.delta`; `Domain([dims])` or
  `Domain(lower, upper, num_cells)`; `State(domain, num_eqn, num_aux)` with `.q`, `.aux`,
  `.problem_data`, `.grid` (`.x`/named dimension, `.p_centers`); `Solution(state, domain)` or
  `Solution(num_eqn, domain)`.
- `Controller`: `solver`, `solution`, `tfinal`, `num_output_times`, `keep_copy`, `output_format`,
  `verbosity`, `run()`, `frames[i].q`/`.t`/`.grid`, `grid`.
- Riemann solvers, all vectorized with the signature
  `(q_l, q_r, aux_l, aux_r, problem_data) -> (wave, s, amdq, apdq)`:
  - `acoustics_1D`
  - `burgers_1D` / `burgers_1D_py.burgers_1D` (with `efix`)
  - `shallow_roe_with_efix_1D`, `shallow_hlle_1D`, `shallow_roe_tracer_1D`
  - `euler_1D_py.euler_roe_1D`, `euler_1D_py.euler_hll_1D`, `euler_with_efix_1D`
  - `traffic_vc_1D`, `traffic_vc_fwave_1D`
  - `nonlinear_elasticity_1D_py.nonlinear_elasticity_1D` (f-wave)
  - plus the `*_constants` modules (index names and `num_eqn`)

## Layout
```
miniclaw/
├── __init__.py     # public names; `pyclaw` alias namespace
├── grid.py         # Dimension, Domain, State, Solution
├── solver.py       # ClawSolver1D: ghost cells/BCs, CFL time step, wave propagation, source splitting
├── limiters.py     # minmod, superbee, van Leer, MC
├── sharpclaw.py    # SharpClawSolver1D (last)
├── controller.py   # Controller: run to output times, frames
├── riemann/        # one module per system
└── visclaw/        # ianimate: Clawpack's 1D animation of a run's frames (Kitchen_sink_problem)
```

## Algorithm
Clawpack wave propagation (LeVeque 2002, chapters 6 and 15):
Q_i -= dt/dx (A+dQ_{i-1/2} + A-dQ_{i+1/2}) + dt/dx (F_{i+1/2} - F_{i-1/2}),
with F = 1/2 sum |s| (1 - dt/dx |s|) W_limited (f-waves: sign(s) instead of |s|).
- 2 ghost cells.
- Variable dt targeting `cfl_desired`; the step is redone if it exceeds `cfl_max`.
- Output times are hit exactly.
- Godunov splitting for `step_source`.

## Tests
- **Riemann solvers:**
  - With q_l = q_r there are no waves.
  - The waves sum to the jump (f-waves sum to the flux jump).
  - amdq + apdq = f(q_r) - f(q_l).
  - Roe resolves an isolated shock exactly.
  - The entropy fix only acts at transonic rarefactions.
  - HLL speeds bound the exact speeds.
- **Solver:**
  - Mass is conserved to machine precision with periodic BCs.
  - Advection at CFL = 1 is exact.
  - Every limiter keeps the solution TVD.
  - Wall, extrapolation and periodic BCs behave correctly.
  - Output times are hit exactly.
  - The source term gives the correct decay.
  - f-wave and wave forms agree for constant coefficients.
- **Convergence:** L1 error to the exact solvers decreases with refinement.
- **Reference:** agreement with the real PyClaw `.npz` reference results.

## Implementation notes
- The step-size rule follows PyClaw exactly, including rejecting and retrying steps and shortening
  the last step to hit output times. This is what makes results bit-identical to Clawpack; don't
  change it. Fixed-dt mode uses a whole number of equal steps per output interval.
- The CFL number is taken over the num_cells + 1 grid edges, as in Clawpack's Fortran `step1`.
- f-wave correction uses sign(s) = +1 at s = 0, like Fortran `dsign`.
- Riemann solvers carry `num_eqn`, `num_waves` and `fwave` attributes (`riemann/solver_info.py`).
  PyClaw gets these from a table keyed by solver name.
- Variants that mirror both Clawpack versions keep both names: `burgers_1D` (Fortran, entropy fix
  on by default) and `burgers_1D_py.burgers_1D` (entropy fix only if `problem_data['efix']`).
- Wave contributions are summed family by family in order (`solver_info.wave_sum`), like Clawpack;
  `einsum` can change the last bits.
- `shallow_roe_tracer_1D` deliberately differs from Clawpack's Fortran, which has a bug in its
  tracer fluctuation (see `CHANGES.md`).
- `tests/reference/book_setups.py` holds the book's runs once; use `book_setups.use(pyclaw, riemann)`
  to pick Clawpack or miniclaw. New reference runs go there.
- `SharpClawSolver1D` follows PyClaw's Python SharpClaw kernel with its defaults: WENO5 from
  `recon.weno` (PyClaw's `reconstruct` module fails to import and PyClaw falls back to it),
  no characteristic decomposition, SSP104, `cfl_desired`/`cfl_max` = 2.45/2.5. As in PyClaw, a too-large
  `dt_initial` makes the first (rejected) step overflow, with RuntimeWarnings; results are unaffected.
