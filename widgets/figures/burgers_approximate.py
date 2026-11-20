"""
Interactive figures of the chapter Burgers_approximate, for the web book (utils.live_figure).
setup() is the chapter's own function, verbatim; frames() runs the cell's three examples and
returns its plot_frame, drawn on a live figure.
"""
from exact_solvers import burgers
from utils import riemann_tools
from utils.live_figure import InteractiveFigure, TimeFigure, slider


def setup(q_l, q_r, N=500, efix=False):

    from miniclaw import pyclaw
    from miniclaw import riemann

    rs = riemann.burgers_1D_py.burgers_1D
    solver = pyclaw.ClawSolver1D(rs)
    solver.order = 1
    solver.kernel_language = 'Python'

    solver.bc_lower[0]=pyclaw.BC.extrap
    solver.bc_upper[0]=pyclaw.BC.extrap

    x = pyclaw.Dimension(-1.0,1.0,N,name='x')
    domain = pyclaw.Domain([x])
    state = pyclaw.State(domain,1)

    state.problem_data['efix'] = efix

    xc = state.grid.p_centers[0]

    state.q[0 ,:] = (xc<=0)*q_l + (xc>0)*q_r

    claw = pyclaw.Controller()
    claw.tfinal = 0.5
    claw.solution = pyclaw.Solution(state,domain)
    claw.solver = solver
    claw.keep_copy = True
    claw.verbosity=0

    return claw


def frames(efix=False, N=200):
    """The cell's shock, rarefaction and transonic rarefaction (with or without the entropy
    fix): runs them and returns its plot_frame(i), drawn on a live figure (only the curves,
    titles and time lines move with the frame i)."""
    shock = setup(2.,1.,N=N,efix=efix)
    shock.run()
    shocksol = burgers.exact_riemann_solution(2.,1.)

    raref = setup(1.,2.,N=N,efix=efix)
    raref.run()
    rarefsol = burgers.exact_riemann_solution(1.,2.)

    transonic = setup(-1.,2.,N=N,efix=efix)
    transonic.run()
    transonicsol = burgers.exact_riemann_solution(-1.,2.)

    runs = [shock, raref, transonic]
    names = ['Shock', 'Rarefaction', 'Transonic rarefaction']

    def draw(fig, i):
        """The cell's plot_frame(i) on fig; returns at_time(i) (utils.live_figure.TimeFigure)."""
        axes = fig.subplots(2,3)
        for ax in axes[0]:
            ax.set_xlim((-1,1)); ax.set_ylim((-1.1,2.1))
        curves = [ax.plot(run.frames[0].grid.x.centers, run.frames[i].q[0,:],'-k',lw=2)[0]
                  for ax, run in zip(axes[1], runs)]
        for ax, sol in zip(axes[0], [shocksol, rarefsol, transonicsol]):
            riemann_tools.plot_waves(*sol,ax=ax,t=i/10.)
        time_lines = [ax.lines[-1] for ax in axes[0]]          # drawn last by plot_waves

        def at_time(i):
            t = i/10.
            for curve, run, line, ax, name in zip(curves, runs, time_lines, axes[1], names):
                curve.set_ydata(run.frames[i].q[0,:])
                line.set_ydata([t, t])
                ax.set_title(name + '(t=' + str(t) + ')')
            return curves + time_lines + [ax.title for ax in axes[1]]
        at_time(i)
        fig.tight_layout()                # once: the titles keep their length
        return at_time

    figure = TimeFigure(draw, (8,4), live=('i',))

    def plot_frame(i):
        figure.show(i=i)
    plot_frame.live_figure = lambda: TimeFigure(draw, (8,4), live=('i',))
    return plot_frame


FRAMES = InteractiveFigure.redraw(
    frames, [slider('i', 0, 10, 5, label='Frame', integer=True)], factory=True)
