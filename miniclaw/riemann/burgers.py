"""Roe solver for Burgers' equation q_t + (q^2/2)_x = 0.

The single wave is the jump W = q_r - q_l with the Rankine-Hugoniot speed
s = (q_l + q_r)/2. At a transonic rarefaction (q_l < 0 < q_r) the entropy fix
splits the flux difference at the sonic point q = 0:
A-dQ = f(0) - f(q_l) = -q_l^2/2 and A+dQ = f(q_r) - f(0) = q_r^2/2.
"""

import numpy as np

from miniclaw.riemann.solver_info import riemann_solver


def _burgers(q_l, q_r, efix):
    wave = (q_r - q_l)[:, np.newaxis, :]
    s = 0.5 * (q_l + q_r)
    amdq = np.minimum(s, 0.0) * wave[:, 0, :]
    apdq = np.maximum(s, 0.0) * wave[:, 0, :]
    if efix:
        transonic = (q_l[0] < 0.0) & (q_r[0] > 0.0)
        amdq[0, transonic] = -0.5 * q_l[0, transonic]**2
        apdq[0, transonic] = 0.5 * q_r[0, transonic]**2
    return wave, s, amdq, apdq


@riemann_solver(num_eqn=1, num_waves=1)
def burgers_1D(q_l, q_r, aux_l, aux_r, problem_data):
    """As Clawpack's Fortran burgers_1D: entropy fix on unless problem_data['efix'] is False."""
    return _burgers(q_l, q_r, problem_data.get('efix', True))


@riemann_solver(num_eqn=1, num_waves=1)
def burgers_1D_py(q_l, q_r, aux_l, aux_r, problem_data):
    """As Clawpack's burgers_1D_py.burgers_1D: entropy fix only if problem_data['efix'] is True."""
    return _burgers(q_l, q_r, problem_data.get('efix', False))
