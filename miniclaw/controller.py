"""Controller: runs a solver to a sequence of output times, as PyClaw's Controller does."""

import copy

import numpy as np


class Controller:
    """Run ``solver`` on ``solution`` from its current time to ``tfinal``.

    The solution is saved at ``num_output_times`` equally spaced times after the
    initial one; with ``keep_copy = True`` these frames are kept in ``frames``.
    """

    def __init__(self):
        self.solver = None
        self.solution = None
        self.tfinal = 1.0
        self.num_output_times = 10
        self.keep_copy = False
        self.output_format = None   # accepted for compatibility; nothing is written to disk
        self.verbosity = 0          # accepted for compatibility
        self.frames = []

    @property
    def grid(self):
        return self.solution.state.grid

    def run(self):
        output_times = np.linspace(self.solution.t, self.tfinal, self.num_output_times + 1)
        self.solver.dt = None   # start from dt_initial
        self.frames = []
        self._save_frame()
        for t in output_times[1:]:
            self.solver.evolve_to_time(self.solution, t)
            self._save_frame()
        return {'cfl': self.solver.cfl}

    def _save_frame(self):
        if self.keep_copy:
            self.frames.append(copy.deepcopy(self.solution))
