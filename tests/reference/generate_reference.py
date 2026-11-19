"""Generate reference results with the real Clawpack/PyClaw, for testing miniclaw.

This script needs Clawpack (e.g. `pip install clawpack` with a Fortran compiler, or
`conda install -c conda-forge clawpack`). Clawpack is NOT a dependency of the book;
run this script in a separate environment:

    python tests/reference/generate_reference.py

It re-runs the PyClaw setups used in the book's chapters (book_setups.py, copied from
the notebooks of clawpack/riemann_book, master) and saves the solution frames as compressed .npz files
next to this script. Each file holds:
    x : cell centers, t : output times, q : frames, shape (num_frames, num_eqn, num_cells)
It also saves pointwise outputs of Clawpack's Python Riemann solvers (riemann_py.npz).
"""

import os

import numpy as np

import clawpack
from clawpack import pyclaw, riemann

import book_setups

book_setups.use(pyclaw, riemann)

HERE = os.path.dirname(os.path.abspath(__file__))


def save(name, claw, every=1, **extra):
    """Save the frames of a finished PyClaw run."""
    frames = claw.frames[::every]
    np.savez_compressed(os.path.join(HERE, name + '.npz'),
                        x=claw.frames[0].grid.p_centers[0],
                        t=np.array([f.t for f in frames]),
                        q=np.array([f.q for f in frames]),
                        clawpack_version=clawpack.__version__, **extra)
    print(f"saved {name}.npz ({len(frames)} frames)")


# --- Pointwise Python Riemann solvers ------------------------------------------------
def riemann_py():
    """Outputs (wave, s, amdq, apdq) of Clawpack's Python Riemann solvers on sample states."""
    rng = np.random.default_rng(2026)
    out = {}

    def record(name, solver, q_l, q_r, aux_l, aux_r, problem_data):
        wave, s, amdq, apdq = solver(q_l, q_r, aux_l, aux_r, problem_data)
        for key, val in dict(q_l=q_l, q_r=q_r, aux_l=aux_l, aux_r=aux_r, wave=wave, s=s,
                             amdq=amdq, apdq=apdq).items():
            out[f"{name}__{key}"] = val

    n = 20
    # Burgers, with and without entropy fix (includes transonic rarefactions)
    q_l, q_r = rng.uniform(-2, 2, (1, n)), rng.uniform(-2, 2, (1, n))
    for efix in (False, True):
        record(f"burgers_efix{efix}", riemann.burgers_1D_py.burgers_1D, q_l, q_r,
               np.zeros((1, n)), np.zeros((1, n)), {'efix': efix})
    # Acoustics
    q_l, q_r = rng.uniform(-1, 1, (2, n)), rng.uniform(-1, 1, (2, n))
    rho, bulk = 2.0, 0.5
    record("acoustics", riemann.acoustics_1D_py.acoustics_1D, q_l, q_r, np.zeros((1, n)),
           np.zeros((1, n)), {'rho': rho, 'bulk': bulk, 'zz': np.sqrt(rho * bulk),
                              'cc': np.sqrt(bulk / rho)})
    # Euler: Roe (with and without entropy fix) and HLL
    gamma = 1.4

    def euler_states():
        rho = rng.uniform(0.5, 2, n)
        u = rng.uniform(-1, 1, n)
        p = rng.uniform(0.5, 2, n)
        return np.array([rho, rho * u, p / (gamma - 1) + 0.5 * rho * u**2])

    q_l, q_r = euler_states(), euler_states()
    # (Clawpack's Python euler_roe_1D has no entropy fix.)
    for name, solver in [("euler_roe", riemann.euler_1D_py.euler_roe_1D),
                         ("euler_hll", riemann.euler_1D_py.euler_hll_1D)]:
        record(name, solver, q_l, q_r, np.zeros((1, n)), np.zeros((1, n)),
               {'gamma': gamma, 'gamma1': gamma - 1, 'efix': False})
    # Shallow water: Roe, HLL
    h_l, h_r = rng.uniform(0.5, 3, n), rng.uniform(0.5, 3, n)
    q_l = np.array([h_l, h_l * rng.uniform(-1, 1, n)])
    q_r = np.array([h_r, h_r * rng.uniform(-1, 1, n)])
    for name, solver in [("shallow_roe", riemann.shallow_1D_py.shallow_roe_1D),
                         ("shallow_hll", riemann.shallow_1D_py.shallow_hll_1D)]:
        record(name, solver, q_l, q_r, np.zeros((1, n)), np.zeros((1, n)),
               {'grav': 1.0, 'efix': False})
    # Nonlinear elasticity (f-wave), with different materials on each side
    q_l = np.array([rng.uniform(0, 0.5, n), rng.uniform(-1, 1, n)])
    q_r = np.array([rng.uniform(0, 0.5, n), rng.uniform(-1, 1, n)])
    aux_l = np.tile(np.array([[1.], [5.], [1.]]), n)
    aux_r = np.tile(np.array([[1.], [2.], [1.]]), n)
    record("nonlinear_elasticity", riemann.nonlinear_elasticity_1D_py.nonlinear_elasticity_1D,
           q_l, q_r, aux_l, aux_r, {'stress_relation': 'quadratic'})

    np.savez_compressed(os.path.join(HERE, 'riemann_py.npz'),
                        clawpack_version=clawpack.__version__, **out)
    print("saved riemann_py.npz")


if __name__ == '__main__':
    for q_l, q_r, name in [(2., 1., 'shock'), (1., 2., 'raref'), (-1., 2., 'transonic')]:
        for efix in (False, True):
            save(f"burgers_approximate_{name}_efix{efix}", book_setups.burgers_approximate(q_l, q_r, efix=efix))
    for rs in ('roe', 'hlle'):
        save(f"fv_compare_shallow_{rs}", book_setups.shallow_dam_break(rs))
    for rs in ('Roe', 'HLL'):
        save(f"fv_compare_shocktube_{rs}_classic", book_setups.shocktube(rs, 'classic'))
        save(f"fv_compare_shocktube_{rs}_sharpclaw", book_setups.shocktube(rs, 'sharpclaw'))
        save(f"fv_compare_blastwave_{rs}", book_setups.blastwave(rs))
    for rho_l, rho_r, v_l, v_r in [(0.7, 0.5, 1.0, 1.5), (0.7, 0.2, 1.0, 1.0)]:
        for rs in ('traffic_vc_1D', 'traffic_vc_fwave_1D'):
            save(f"traffic_variable_speed_{rho_l}_{rho_r}_{v_l}_{v_r}_{rs}",
                 book_setups.traffic_variable_speed(rho_l, rho_r, v_l, v_r, getattr(riemann, rs)))
    save("kitchen_sink", book_setups.kitchen_sink(), every=5)
    save("kitchen_sink_constant_initial_data", book_setups.kitchen_sink(constant_initial_data=True), every=5)
    save("acoustics_bump", book_setups.acoustics_bump(), every=5)
    save("burgers_bump", book_setups.burgers_bump(), every=5)
    riemann_py()
