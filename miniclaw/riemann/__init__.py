"""Pointwise approximate Riemann solvers, vectorized over interfaces.

Every solver has the Clawpack signature

    wave, s, amdq, apdq = solver(q_l, q_r, aux_l, aux_r, problem_data)

where q_l, q_r have shape (num_eqn, n) (the states left and right of n interfaces),
wave has shape (num_eqn, num_waves, n), s has shape (num_waves, n), and amdq, apdq
are the left- and right-going fluctuations A-dQ and A+dQ. Each solver also has the
attributes num_eqn, num_waves and fwave. The names mirror ``clawpack.riemann``.
"""

from types import SimpleNamespace

from miniclaw.riemann.acoustics import acoustics_1D
from miniclaw.riemann.burgers import burgers_1D, burgers_1D_py

# Same access paths as clawpack.riemann, e.g. riemann.burgers_1D_py.burgers_1D
burgers_1D_py = SimpleNamespace(burgers_1D=burgers_1D_py, num_eqn=1, num_waves=1)
