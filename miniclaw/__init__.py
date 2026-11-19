"""miniclaw: a minimal, pure-Python educational reimplementation of the 1D
Clawpack/PyClaw algorithms used in the book "Riemann Problems and Jupyter
Solutions". It is NOT Clawpack itself; for real computations use Clawpack
(www.clawpack.org).

The interface mirrors a small subset of PyClaw, so that code written for the
book reads like PyClaw code:

    from miniclaw import pyclaw, riemann
    solver = pyclaw.ClawSolver1D(riemann.burgers_1D)
"""

from miniclaw import pyclaw, riemann  # noqa: F401
from miniclaw.controller import Controller  # noqa: F401
from miniclaw.grid import Dimension, Domain, Grid, Solution, State  # noqa: F401
from miniclaw.solver import BC, ClawSolver1D  # noqa: F401
