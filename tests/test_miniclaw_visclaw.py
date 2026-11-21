"""miniclaw.visclaw.ianimate: the animation of a run (Kitchen_sink_problem)."""
import matplotlib

matplotlib.use('Agg')

import numpy as np  # noqa: E402
from matplotlib import animation  # noqa: E402

from miniclaw import pyclaw, riemann  # noqa: E402
from miniclaw.visclaw.ianimate import ianimate  # noqa: E402


def dam_break():
    """A short shallow water dam break with 5 output times."""
    solver = pyclaw.ClawSolver1D(riemann.shallow_roe_with_efix_1D)
    solver.bc_lower[0] = solver.bc_upper[0] = pyclaw.BC.extrap
    x = pyclaw.Dimension(-1., 1., 100, name='x')
    domain = pyclaw.Domain([x])
    state = pyclaw.State(domain, solver.num_eqn)
    state.problem_data['grav'] = 1.
    xc = state.grid.p_centers[0]
    state.q[0, :] = np.where(xc < 0, 2., 1.)
    state.q[1, :] = 0.
    claw = pyclaw.Controller()
    claw.solver, claw.solution = solver, pyclaw.Solution(state, domain)
    claw.tfinal, claw.num_output_times, claw.keep_copy, claw.verbosity = 0.4, 5, True, 0
    claw.run()
    return claw


def test_ianimate_shows_every_frame():
    claw = dam_break()
    anim = ianimate(claw)
    assert isinstance(anim, animation.FuncAnimation)           # the chapter calls anim.to_jshtml()
    fig = anim._fig
    line = fig.axes[0].lines[0]
    xc = claw.frames[0].state.grid.p_centers[0]
    for i, frame in enumerate(claw.frames):
        anim._func(i)
        assert np.array_equal(line.get_xdata(), xc) and np.array_equal(line.get_ydata(), frame.q[0])
        assert fig._suptitle.get_text() == 'Time t = %.2f' % frame.t      # e.g. 'Time t = 0.30'
    # the depth stays between 1 and 2: the y range is 10% wider on each side
    assert fig.axes[0].get_ylim() == (0.9, 2.1)
    assert fig.axes[0].get_xlim() == (xc[0], xc[-1])
    assert '<img' in anim.to_jshtml() or 'animation' in anim.to_jshtml()


def test_ianimate_size_and_frame_interval():
    """figsize and interval (ms per frame) reach the animation; by default 10 x 6 and 200 ms."""
    claw = dam_break()
    default, chosen = ianimate(claw), ianimate(claw, figsize=(6.4, 4.8), interval=60)
    assert tuple(default._fig.get_size_inches()) == (10, 6) and default._interval == 200
    assert tuple(chosen._fig.get_size_inches()) == (6.4, 4.8) and chosen._interval == 60
