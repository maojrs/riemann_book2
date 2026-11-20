"""
Interactive figures of Traffic_with_ramps, for the web book (utils.live_figure).
The chapter defines its plotting functions in its own cells; riemann_plot draws its
plot_function(t) on a live figure (a new time only moves the time line and the density).
"""
from exact_solvers import traffic_ramps
from utils import riemann_tools
from utils.live_figure import InteractiveFigure, TimeFigure, slider
from utils.riemann_figure import plot_riemann_at_time


def c(rho, xi):
    return (1.-2*rho)


def riemann_plot(rho_l, rho_r, D):
    """The chapter's make_plot_function(rho_l, rho_r, D): its plot_function(t)."""
    states, speeds, reval, wave_types = traffic_ramps.exact_riemann_solution(rho_l,rho_r,D)

    def draw(fig, t):
        ax, at_time = plot_riemann_at_time(states, speeds, reval, wave_types, t, fig=fig, t_pointer=0,
                                           extra_axes=True, variable_names=['Density'])
        riemann_tools.plot_characteristics(reval,c,None,ax[0])
        traffic_ramps.phase_plane_plot(rho_l,rho_r,D,axes=ax[2],show=False)
        ax[1].set_ylim(0,1)
        return at_time

    def plot_function(t):
        figure.show(t=t)
    plot_function.live_figure = lambda: TimeFigure(draw, (9, 3))
    figure = plot_function.live_figure()
    return plot_function


def plot_all(rho_l,rho_r,D):
    """The chapter's plot_all, verbatim (all of it changes with the sliders)."""
    import matplotlib.pyplot as plt
    states, speeds, reval, wave_types = traffic_ramps.exact_riemann_solution(rho_l,rho_r,D)
    ax = riemann_tools.plot_riemann(states,speeds,reval,wave_types,t=0.5,extra_axes=2);
    riemann_tools.plot_characteristics(reval,c,None,ax[0])
    traffic_ramps.phase_plane_plot(rho_l,rho_r,D,axes=ax[2],show=False)
    traffic_ramps.plot_car_trajectories(rho_l,rho_r,D,axes=ax[3])

    plt.show()


RIEMANN = InteractiveFigure.redraw(riemann_plot, [slider('t', 0., 0.9, 0.1)], factory=True)
ALL = InteractiveFigure.redraw(
    plot_all,
    [slider('rho_l', 0., 1., 0.4, label=r'$\rho_l$', step=0.01),
     slider('rho_r', 0., 1., 0.7, label=r'$\rho_r$', step=0.01),
     slider('D', 0., 0.25, 0.1, step=0.01)],
    [['rho_l', 'rho_r'], ['D']])
