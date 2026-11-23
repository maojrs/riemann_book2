"""f-wave Riemann solver for nonlinear elasticity in heterogeneous media,
    eps_t - u_x = 0,   (rho u)_t - sigma(eps, x)_x = 0,
with q = (eps, rho u), as Clawpack's nonlinear_elasticity_1D_py. The material is
aux = (rho, K) for sigma = exp(K eps) - 1 (default) or aux = (rho, K1, K2) for
sigma = K1 eps + K2 eps^2 (problem_data['stress_relation'] = 'quadratic').

The flux jump is split into f-waves along the eigenvectors (1, Z_l) and (1, -Z_r),
with impedances Z = rho c and sound speeds c = sqrt(sigma'(eps)/rho) on each side.
"""

import numpy as np

from miniclaw.riemann.solver_info import riemann_solver


def sigma(q, aux, problem_data):
    """Stress as a function of strain."""
    if problem_data.get('stress_relation', 'exponential') == 'quadratic':
        return aux[1] * q[0] + aux[2] * q[0]**2
    return np.exp(aux[1] * q[0]) - 1.0


def dsigma(q, aux, problem_data):
    """Derivative of the stress with respect to strain."""
    if problem_data.get('stress_relation', 'exponential') == 'quadratic':
        return aux[1] + 2 * aux[2] * q[0]
    return aux[1] * np.exp(aux[1] * q[0])


@riemann_solver(num_eqn=2, num_waves=2, fwave=True)
def nonlinear_elasticity_1D(q_l, q_r, aux_l, aux_r, problem_data):
    rho_l, rho_r = aux_l[0], aux_r[0]
    c_l = np.sqrt(dsigma(q_l, aux_l, problem_data) / rho_l)
    c_r = np.sqrt(dsigma(q_r, aux_r, problem_data) / rho_r)
    Z_l, Z_r = c_l * rho_l, c_r * rho_r
    du = q_r[1] / rho_r - q_l[1] / rho_l
    dsig = sigma(q_r, aux_r, problem_data) - sigma(q_l, aux_l, problem_data)
    b1 = -(Z_r * du + dsig) / (Z_r + Z_l)
    b2 = -(Z_l * du - dsig) / (Z_r + Z_l)
    fwave = np.array([[b1, b2],
                      [b1 * Z_l, b2 * (-Z_r)]])
    s = np.array([-c_l, c_r])
    return fwave, s, fwave[:, 0, :].copy(), fwave[:, 1, :].copy()
