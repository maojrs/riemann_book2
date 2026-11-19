"""Exact (linear) Riemann solver for acoustics, p_t + K u_x = 0, rho u_t + p_x = 0.

With impedance Z = rho c and sound speed c = sqrt(K/rho) (problem_data 'zz' and 'cc'),
the jump dq = q_r - q_l splits into W1 = a1 (-Z, 1) with speed -c and W2 = a2 (Z, 1)
with speed c, where a1 = (-dp + Z du)/(2Z), a2 = (dp + Z du)/(2Z).
"""

import numpy as np

from miniclaw.riemann.solver_info import riemann_solver


@riemann_solver(num_eqn=2, num_waves=2)
def acoustics_1D(q_l, q_r, aux_l, aux_r, problem_data):
    Z, c = problem_data['zz'], problem_data['cc']
    dp, du = q_r[0] - q_l[0], q_r[1] - q_l[1]
    a1 = (-dp + Z * du) / (2 * Z)
    a2 = (dp + Z * du) / (2 * Z)
    wave = np.array([[-a1 * Z, a2 * Z],
                     [a1, a2]])                       # (num_eqn, num_waves, n)
    s = np.array([np.full_like(dp, -c), np.full_like(dp, c)])
    amdq = s[0] * wave[:, 0, :]
    apdq = s[1] * wave[:, 1, :]
    return wave, s, amdq, apdq
