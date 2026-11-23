"""SharpClaw: high-order wave-propagation (method of lines), as PyClaw's SharpClawSolver1D
with its defaults (Ketcheson, Parsani & LeVeque, SIAM J. Sci. Comput. 35, 2013):

- WENO5 reconstruction of each component of q at the cell edges;
- Riemann problems at the edges between reconstructed values (fluctuations A-dQ, A+dQ),
  plus the "total fluctuation" inside each cell between its own edge values;
- the 10-stage, 4th-order strong-stability-preserving Runge-Kutta method SSP(10,4).

The semi-discrete scheme is
    dQ_i/dt = -1/dx (A+dQ_{i-1/2} + A-dQ_{i+1/2} + A dQ_i),
where A dQ_i is the total fluctuation between the edge values inside cell i.
"""

import copy

import numpy as np

from miniclaw.solver import ClawSolver1D


def weno5(q):
    """Fifth-order WENO reconstruction, component by component (as PyClaw's recon.weno).

    Returns (ql, qr): the values at the left and right edges of each cell. Cells too close
    to the ends of the array keep their cell averages."""
    epweno = 1.e-36
    dqiph = np.diff(q, 1)
    LL, UL = 3, q.shape[1] - 2
    qr, ql = q.copy(), q.copy()
    for im in (1, -1):              # im = +1: right edge values, im = -1: left edge values
        dq_intwo = dqiph[:, LL - 2 * im - 1:UL - 2 * im - 1]
        dq_ione = dqiph[:, LL + im - 1:UL + im - 1]
        dq_inone = dqiph[:, LL - im - 1:UL - im - 1]
        dq = dqiph[:, LL - 1:UL - 1]
        t1 = im * (dq_intwo - dq_inone)
        t2 = im * (dq_inone - dq)
        t3 = im * (dq - dq_ione)
        # Smoothness indicators of the three candidate stencils, squared
        tt1 = (epweno + (13. * t1**2 + 3. * (dq_intwo - 3. * dq_inone)**2))**2
        tt2 = (epweno + (13. * t2**2 + 3. * (dq_inone + dq)**2))**2
        tt3 = (epweno + (13. * t3**2 + 3. * (3. * dq - dq_ione)**2))**2
        # Nonlinear weights (ideal weights 1/10, 6/10, 3/10)
        s1 = tt2 * tt3
        s2 = 6. * tt1 * tt3
        s3 = 3. * tt1 * tt2
        t0 = 1. / (s1 + s2 + s3)
        s1 *= t0
        s3 *= t0
        z = (s1 * (t2 - t1) + (0.5 * s3 - 0.25) * (t3 - t2)) / 3. \
            + (-q[:, LL - 2:UL - 2] + 7. * (q[:, LL - 1:UL - 1] + q[:, LL:UL]) - q[:, LL + 1:UL + 1]) / 12.
        if im == 1:
            qr[:, LL - 1:UL - 1] = z
        else:
            ql[:, LL:UL] = z
    return ql, qr


class SharpClawSolver1D(ClawSolver1D):
    """SharpClaw solver; boundary conditions and attributes as ClawSolver1D.

    Only the defaults used in the book are implemented: WENO5 without characteristic
    decomposition, SSP104 time stepping and a variable time step."""

    num_ghost = 3

    def __init__(self, riemann_solver=None):
        super().__init__(riemann_solver)
        self.cfl_desired = 2.45     # PyClaw's defaults for SSP104
        self.cfl_max = 2.5
        self.time_integrator = 'SSP104'
        self._dq_dt = None
        self._dt_old = None
        self._accepted = True

    def dq_hyperbolic(self, state, dt):
        """Return dt * dQ/dt for the interior cells, and the Courant number."""
        g = self.num_ghost
        num_cells = state.grid.num_cells[0]
        dtdx = dt / state.grid.delta[0]
        qbc, auxbc = self._with_ghost_cells(state)
        aux_l = None if auxbc is None else auxbc[:, :-1]
        aux_r = None if auxbc is None else auxbc[:, 1:]
        ql, qr = weno5(qbc)

        # Riemann problems at the cell edges, between the reconstructed values
        _, s, amdq, apdq = self.rp(qr[:, :-1], ql[:, 1:], aux_l, aux_r, state.problem_data)
        LL, UL = g - 1, num_cells + g + 1
        cfl = dtdx * np.max(np.abs(s[:, LL - 1:UL - 1]))
        # Total fluctuation inside each cell, between its left and right edge values
        _, _, amdq2, apdq2 = self.rp(ql, qr, auxbc, auxbc, state.problem_data)

        dq = -dtdx * (amdq[:, LL:UL] + apdq[:, LL - 1:UL - 1] + apdq2[:, LL:UL] + amdq2[:, LL:UL])
        return dq[:, 1:1 + num_cells], cfl

    def _dq(self, stage):
        """dt * dQ/dt at a Runge-Kutta stage, keeping track of the largest Courant number."""
        dq, cfl = self.dq_hyperbolic(stage, self.dt)
        self.cfl = max(self.cfl, cfl)
        return dq

    def _ssp104(self, state):
        """Ketcheson's SSP(10,4) Runge-Kutta step, written in its low-storage form."""
        dt = self.dt
        stage = copy.copy(state)
        stage.q = state.q + dt * self._dq_dt / 6.
        stage.t = state.t + dt / 6.
        for _ in range(4):
            stage.q = stage.q + self._dq(stage) / 6.
            stage.t = stage.t + dt / 6.
        state.q = state.q / 25. + 0.36 * stage.q
        stage.q = 15. * state.q - 5. * stage.q
        stage.t = state.t + dt / 3.
        for _ in range(4):
            stage.q = stage.q + self._dq(stage) / 6.
            stage.t = stage.t + dt / 6.
        state.q = state.q + (0.6 * stage.q + 0.1 * self._dq(stage))

    def evolve_to_time(self, solution, tend):
        """Take steps until solution.t == tend (PyClaw's step-size control for SharpClaw)."""
        state = solution.state
        tstart = state.t
        if self.dt is None:                     # start of a run
            self.dt, self._dt_old, self._accepted = self.dt_initial, None, True
        for _ in range(self.max_steps):
            q_backup = state.q.copy()
            if self._accepted:                  # dQ/dt at the start of the step
                dq, self.cfl = self.dq_hyperbolic(state, self.dt)
                self._dq_dt = dq / self.dt
            # New dt from the last Courant number; that number is rescaled to the new dt.
            if self._dt_old is None:
                self._dt_old = self.dt
            elif self.cfl > 0:
                self._dt_old = self.dt
                self.dt = self.dt * self.cfl_desired / self.cfl
            else:
                self.dt = self.dt_max
            if state.t + self.dt > tend and tstart < tend:
                self.dt = tend - state.t
            if tend - state.t - self.dt < 1e-14 * state.t:
                self.dt = tend - state.t
            self.cfl = self.dt / self._dt_old * self.cfl
            self._dt_old = self.dt
            self._ssp104(state)
            self._accepted = self.cfl <= self.cfl_max
            if self._accepted:
                state.t += self.dt
            else:
                state.q = q_backup              # reject; retry with a smaller dt
            if state.t >= tend:
                return
        raise RuntimeError("Maximum number of time steps reached")
