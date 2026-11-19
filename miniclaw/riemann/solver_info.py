"""Attach num_eqn, num_waves and fwave to a Riemann solver function."""


def riemann_solver(num_eqn, num_waves, fwave=False):
    def decorate(solver):
        solver.num_eqn, solver.num_waves, solver.fwave = num_eqn, num_waves, fwave
        return solver
    return decorate
