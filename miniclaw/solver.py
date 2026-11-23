"""The classic Clawpack wave-propagation solver in 1D (PyClaw's ClawSolver1D).

One step for q_t + f(q)_x = 0 (LeVeque, Finite Volume Methods for Hyperbolic
Problems, 2002, Sections 6.13-6.15 and 15.5):

    Q_i -= dt/dx (A+dQ_{i-1/2} + A-dQ_{i+1/2})        Godunov update
    Q_i -= dt/dx (F_{i+1/2} - F_{i-1/2})              high-resolution correction

with F_{i-1/2} = 1/2 sum_p |s_p| (1 - dt/dx |s_p|) W~_p, where W~_p are the
limited waves. For f-waves Z_p, |s_p| W_p is replaced by sign(s_p) Z_p.
The time step adapts to keep the Courant number near ``cfl_desired``; a step
whose Courant number exceeds ``cfl_max`` is redone with a smaller dt.
"""

import numpy as np

from miniclaw.limiters import tvd
from miniclaw.riemann.solver_info import wave_sum


class BC:
    """Boundary condition types."""
    custom = 0
    extrap = 1
    periodic = 2
    wall = 3


class ClawSolver1D:
    """Classic Clawpack solver; the attributes mirror PyClaw's."""

    num_ghost = 2

    def __init__(self, riemann_solver=None):
        self.rp = riemann_solver
        self.num_eqn = getattr(riemann_solver, 'num_eqn', None)
        self.num_waves = getattr(riemann_solver, 'num_waves', None)
        self.fwave = getattr(riemann_solver, 'fwave', False)
        self.order = 2
        self.limiters = tvd.minmod
        self.bc_lower, self.bc_upper = [None], [None]
        self.aux_bc_lower, self.aux_bc_upper = [None], [None]
        self.user_bc_lower = self.user_bc_upper = None
        self.user_aux_bc_lower = self.user_aux_bc_upper = None
        self.reflect_index = [1]       # component negated at walls (the momentum)
        self.step_source = None        # step_source(solver, state, dt), Godunov splitting
        self.cfl_desired = 0.9
        self.cfl_max = 1.0
        self.dt_initial = 0.1
        self.dt_max = 1e99
        self.dt_variable = True
        self.max_steps = 10000
        self.kernel_language = 'Python'  # accepted for compatibility; always Python
        self.dt = None
        self.cfl = 0.0                   # Courant number of the last step

    @property
    def all_bcs(self):
        return self.bc_lower[0]

    @all_bcs.setter
    def all_bcs(self, bc):
        self.bc_lower[0] = self.bc_upper[0] = bc

    # --- Boundary conditions ---------------------------------------------------------
    def _with_ghost_cells(self, state):
        """Arrays qbc (and auxbc) with ghost cells filled according to the boundary conditions."""
        g = self.num_ghost
        qbc = np.pad(state.q, ((0, 0), (g, g)))
        auxbc = None if state.aux is None else np.pad(state.aux, ((0, 0), (g, g)))
        if auxbc is not None:
            self._fill_ghost(auxbc, self.aux_bc_lower[0], 'lower', state, qbc, auxbc, is_q=False)
            self._fill_ghost(auxbc, self.aux_bc_upper[0], 'upper', state, qbc, auxbc, is_q=False)
        self._fill_ghost(qbc, self.bc_lower[0], 'lower', state, qbc, auxbc, is_q=True)
        self._fill_ghost(qbc, self.bc_upper[0], 'upper', state, qbc, auxbc, is_q=True)
        return qbc, auxbc

    def _fill_ghost(self, array, bc, side, state, qbc, auxbc, is_q):
        g = self.num_ghost
        if bc == BC.custom:
            user_bc = {('lower', True): self.user_bc_lower, ('upper', True): self.user_bc_upper,
                       ('lower', False): self.user_aux_bc_lower,
                       ('upper', False): self.user_aux_bc_upper}[(side, is_q)]
            user_bc(state, state.grid.dimensions[0], state.t, qbc, auxbc, g)
            return
        lower = side == 'lower'
        ghost = slice(0, g) if lower else slice(-g, None)
        if bc == BC.extrap:
            array[:, ghost] = array[:, [g]] if lower else array[:, [-g - 1]]
        elif bc == BC.periodic:
            array[:, ghost] = array[:, -2 * g:-g] if lower else array[:, g:2 * g]
        elif bc == BC.wall:
            array[:, ghost] = array[:, 2 * g - 1:g - 1:-1] if lower else array[:, -g - 1:-2 * g - 1:-1]
            if is_q:
                array[self.reflect_index, ghost] *= -1
        else:
            raise ValueError(f"Boundary condition {bc!r} on the {side} side is not set or not supported")

    # --- One step on the homogeneous equation ----------------------------------------
    def step_hyperbolic(self, state, dt):
        """Advance state.q by dt with the wave-propagation method; return the Courant number."""
        g = self.num_ghost
        num_cells = state.grid.num_cells[0]
        dtdx = dt / state.grid.delta[0]
        qbc, auxbc = self._with_ghost_cells(state)

        # Riemann problems at all interfaces; interface k separates cells k and k+1 of qbc.
        aux_l = None if auxbc is None else auxbc[:, :-1]
        aux_r = None if auxbc is None else auxbc[:, 1:]
        wave, s, amdq, apdq = self.rp(qbc[:, :-1], qbc[:, 1:], aux_l, aux_r, state.problem_data)

        edges = slice(g - 1, g + num_cells)          # the num_cells + 1 cell edges of the grid
        cfl = dtdx * np.max(np.abs(s[:, edges]))

        # Godunov update: fluctuations enter the cells on either side of each edge.
        q = qbc.copy()
        q[:, g:g + num_cells + 1] -= dtdx * apdq[:, edges]
        q[:, g - 1:g + num_cells] -= dtdx * amdq[:, edges]

        if self.order == 2:
            limited = tvd.limit(wave, s, self.limiters) if np.any(np.atleast_1d(self.limiters)) else wave
            if self.fwave:
                coef = np.where(s >= 0, 1.0, -1.0)   # f-waves already include the speed
            else:
                coef = np.abs(s)
            weights = 0.5 * coef * (1.0 - dtdx * np.abs(s))           # (num_waves, interfaces)
            F = wave_sum(weights, limited)                             # correction fluxes
            q[:, g:g + num_cells] -= dtdx * (F[:, g:g + num_cells] - F[:, g - 1:g + num_cells - 1])

        state.q = q[:, g:g + num_cells]
        return cfl

    # --- Time stepping ---------------------------------------------------------------
    def _choose_dt(self, t, tstart, tend):
        """PyClaw's step-size rule: rescale the last dt to the desired Courant number,
        and shorten the step to land exactly on tend."""
        if self.dt is None:
            self.dt = self.dt_initial
        else:
            self.dt = min(self.dt_max, self.dt * self.cfl_desired / self.cfl) if self.cfl > 0 else self.dt_max
        if t + self.dt > tend and tstart < tend:
            self.dt = tend - t
        if tend - t - self.dt < 1e-14 * t:
            self.dt = tend - t

    def _step(self, state, dt):
        """One step: hyperbolic update, then the source term (Godunov splitting).
        Returns False, leaving state unchanged, if the Courant number exceeds cfl_max."""
        q_backup = state.q.copy()
        self.cfl = self.step_hyperbolic(state, dt)
        if self.cfl > self.cfl_max:
            state.q = q_backup
            return False
        if self.step_source is not None:
            self.step_source(self, state, dt)
        return True

    def evolve_to_time(self, solution, tend):
        """Take steps until solution.t == tend."""
        state = solution.state
        tstart = state.t
        if not self.dt_variable:
            # A whole number of equal steps of (about) dt_initial.
            num_steps = max(1, round((tend - tstart) / self.dt_initial))
            dt = (tend - tstart) / num_steps
            for n in range(num_steps):
                if not self._step(state, dt):
                    raise RuntimeError("CFL too large with a fixed time step")
                state.t = tstart + (n + 1) * dt
            return
        for _ in range(self.max_steps):
            self._choose_dt(state.t, tstart, tend)
            if self._step(state, self.dt):
                state.t += self.dt
            # otherwise the step was rejected: retry with the smaller dt from _choose_dt
            if state.t >= tend:
                return
        raise RuntimeError("Maximum number of time steps reached")
