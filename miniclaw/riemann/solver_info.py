"""Attach num_eqn, num_waves and fwave to a Riemann solver function."""


def riemann_solver(num_eqn, num_waves, fwave=False):
    def decorate(solver):
        solver.num_eqn, solver.num_waves, solver.fwave = num_eqn, num_waves, fwave
        return solver
    return decorate


def wave_sum(coef, wave):
    """sum_p coef_p W_p, added family by family in order (as Clawpack does, so that
    results agree to the last bit). coef: (num_waves, n), wave: (num_eqn, num_waves, n)."""
    total = coef[0] * wave[:, 0, :]
    for p in range(1, wave.shape[1]):
        total = total + coef[p] * wave[:, p, :]
    return total
