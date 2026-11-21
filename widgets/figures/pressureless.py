"""
Interactive figures of Pressureless_flow, for the web book (utils.live_figure).
The chapter defines its plotting functions in its own cells. riemann_plot draws its plot_function on
a live figure: a new time moves the time line and the curves, and the characteristics are
shown or hidden without building the figure again; a new g draws the solution again on the
same axes. connect_states also keeps its axes and draws their contents again.
"""
import numpy as np

from exact_solvers import shallow_water
from utils import riemann_tools
from utils.live_figure import InteractiveFigure, KeptAxesFigure, TimeFigure, checkbox, slider
from utils.riemann_figure import drawn_by, plot_riemann_at_time, riemann_axes

def connect_states(ax, h_l=1.,u_l=-1.,h_r=1.,u_r=1.,logg=0.,plot_unphysical=True):
    """The chapter's connect_states, on its two axes ax, which are kept from one change to
    the next."""
    g = 10.**logg
    q_l = np.array([h_l,h_l*u_l])
    q_r = np.array([h_r,h_r*u_r])
    shallow_water.phase_plane_curves(q_l[0], q_l[1], 'qleft', g,
                                     wave_family=1, ax=ax[0],
                                     plot_unphysical=plot_unphysical)
    shallow_water.phase_plane_curves(q_r[0], q_r[1], 'qright', g,
                                     wave_family=2, ax=ax[0],
                                     plot_unphysical=plot_unphysical)
    shallow_water.phase_plane_curves(q_l[0], q_l[1], 'qleft', g,
                                     wave_family=1, y_axis='hu',ax=ax[1],
                                     plot_unphysical=plot_unphysical)
    shallow_water.phase_plane_curves(q_r[0], q_r[1], 'qright', g,
                                     wave_family=2, y_axis='hu',ax=ax[1],
                                     plot_unphysical=plot_unphysical)
    ax[0].set_title('h-u plane'); ax[1].set_title('h-hu plane');
    ax[0].set_xlim(0,3); ax[1].set_xlim(0,3);
    ax[0].set_ylim(-10,10); ax[1].set_ylim(-10,10);
    ax[0].figure.tight_layout()


def c1(q, xi, g=1.):
    """Characteristic speed for shallow water 1-waves, u - sqrt(g h) (0 where dry): the
    chapter's c1, for many points at once."""
    h = np.asarray(q[0], dtype=float)
    wet = h > 0
    u = np.divide(q[1], h, out=np.zeros_like(h), where=wet)
    return np.where(wet, u - np.sqrt(g*np.maximum(h, 0)), 0.)

def c2(q, xi, g=1.):
    """Characteristic speed for shallow water 2-waves, u + sqrt(g h) (0 where dry): the
    chapter's c2, for many points at once."""
    h = np.asarray(q[0], dtype=float)
    wet = h > 0
    u = np.divide(q[1], h, out=np.zeros_like(h), where=wet)
    return np.where(wet, u + np.sqrt(g*np.maximum(h, 0)), 0.)


def riemann_plot(q_l, q_r, force_waves=None, extra_lines=None):
    """The chapter's make_plot_function(q_l, q_r): its plot_function(t, logg, plot_1_chars,
    plot_2_chars)."""
    q_l, q_r = np.asarray(q_l, dtype=float), np.asarray(q_r, dtype=float)

    def draw(ax, t, plot_1_chars, plot_2_chars, logg):
        varnames = shallow_water.primitive_variables
        prim = shallow_water.cons_to_prim
        g = 10**logg
        states, speeds, reval, wave_types = \
            shallow_water.exact_riemann_solution(q_l,q_r,g,
                                                 force_waves=force_waves)
        ax, solution_at_time = plot_riemann_at_time(states, speeds, reval, wave_types, t, ax=ax,
                                                    emptied=True, t_pointer=0, extra_axes=True,
                                                    variable_names=varnames,
                                                    derived_variables=prim)
        shallow_water.phase_plane_plot(q_l,q_r,g,ax=ax[3],
                                       force_waves=force_waves,y_axis='u')
        shown = {}

        def characteristics(c, show):               # drawn when first checked, then hidden or shown
            if show and c not in shown:
                shown[c] = drawn_by(ax[:1], lambda: riemann_tools.plot_characteristics(
                    reval, c, (g,g), axes=ax[0], extra_lines=extra_lines))
            for line in shown.get(c, []):          # in the background, under the waves
                line.set_visible(show)

        def at_time(t, plot_1_chars, plot_2_chars):
            characteristics(c1, plot_1_chars)
            characteristics(c2, plot_2_chars)
            return solution_at_time(t)
        return at_time

    def plot_function(t, logg, plot_1_chars=False, plot_2_chars=False):
        figure.show(t=t, logg=logg, plot_1_chars=plot_1_chars, plot_2_chars=plot_2_chars)
    plot_function.live_figure = lambda: TimeFigure(draw, (10, 3), background=('plot_1_chars', 'plot_2_chars'),
                                                   axes=lambda fig: riemann_axes(fig, 4))
    figure = plot_function.live_figure()
    return plot_function


CONNECT_STATES = InteractiveFigure(
    lambda: KeptAxesFigure(lambda fig: fig.subplots(1, 2), connect_states, (8, 4)),
    [slider('h_l', 0.001, 2., 1.), slider('u_l', -5., 5., -1.),
     slider('h_r', 0.001, 2., 1.), slider('u_r', -5., 5., 1.),
     slider('logg', -5., 2., 0., label=r'$\log_{10}(g)$'),
     checkbox('plot_unphysical', True, 'plot_unphysical')],
    [['h_l', 'h_r'], ['u_l', 'u_r'], ['logg'], ['plot_unphysical']])
RIEMANN_SW = InteractiveFigure.redraw(
    riemann_plot,
    [slider('t', 0., 0.9, 0.1), checkbox('plot_1_chars', False, '1-characteristics'),
     checkbox('plot_2_chars', False, '2-characteristics'),
     slider('logg', -10, 2, 0, label=r'$\log_{10}(g)$', integer=True)],
    factory=True)
