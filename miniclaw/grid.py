"""Grid and solution containers, mirroring PyClaw's Dimension, Domain, State and Solution."""

import numpy as np


class Dimension:
    """A uniform 1D grid of ``num_cells`` cells on [lower, upper]."""

    def __init__(self, lower, upper, num_cells, name='x'):
        self.lower, self.upper = float(lower), float(upper)
        self.num_cells = int(num_cells)
        self.name = name

    @property
    def delta(self):
        """Cell width."""
        return (self.upper - self.lower) / self.num_cells

    @property
    def edges(self):
        return np.linspace(self.lower, self.upper, self.num_cells + 1)

    @property
    def centers(self):
        return self.lower + (np.arange(self.num_cells) + 0.5) * self.delta


class Grid:
    """Holds the dimensions; each one is also an attribute named after it (e.g. ``grid.x``)."""

    def __init__(self, dimensions):
        self.dimensions = list(dimensions)
        for dim in self.dimensions:
            setattr(self, dim.name, dim)

    @property
    def p_centers(self):
        return [dim.centers for dim in self.dimensions]

    @property
    def delta(self):
        return [dim.delta for dim in self.dimensions]

    @property
    def num_cells(self):
        return [dim.num_cells for dim in self.dimensions]


class Domain:
    """``Domain(dimension)``, ``Domain([dimension])`` or ``Domain(lower, upper, num_cells)``
    with tuples, as in PyClaw."""

    def __init__(self, *args):
        if len(args) == 3:
            lower, upper, num_cells = args
            dims = [Dimension(lower[0], upper[0], num_cells[0], name='x')]
        else:
            dims = args[0] if isinstance(args[0], (list, tuple)) else [args[0]]
        self.grid = Grid(dims)


class State:
    """Solution values ``q`` (num_eqn x num_cells), auxiliary values ``aux``,
    ``problem_data`` for the Riemann solver, and the time ``t``."""

    def __init__(self, domain, num_eqn, num_aux=0):
        self.grid = domain.grid if isinstance(domain, Domain) else domain
        num_cells = self.grid.num_cells[0]
        self.q = np.zeros((num_eqn, num_cells))
        self.aux = np.zeros((num_aux, num_cells)) if num_aux > 0 else None
        self.problem_data = {}
        self.t = 0.0

    @property
    def num_eqn(self):
        return self.q.shape[0]

    @property
    def num_aux(self):
        return 0 if self.aux is None else self.aux.shape[0]


class Solution:
    """``Solution(state, domain)`` or ``Solution(num_eqn, domain)``. Gives direct access to the
    state's ``q``, ``aux``, ``t``, ``problem_data`` and ``grid``."""

    def __init__(self, state_or_num_eqn, domain):
        if isinstance(state_or_num_eqn, State):
            self.state = state_or_num_eqn
        else:
            self.state = State(domain, state_or_num_eqn)
        self.domain = domain

    @property
    def states(self):
        return [self.state]

    @property
    def q(self):
        return self.state.q

    @q.setter
    def q(self, value):
        self.state.q = value

    @property
    def aux(self):
        return self.state.aux

    @property
    def t(self):
        return self.state.t

    @t.setter
    def t(self, value):
        self.state.t = value

    @property
    def problem_data(self):
        return self.state.problem_data

    @property
    def grid(self):
        return self.state.grid
