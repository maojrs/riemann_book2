"""
Interactive figures of Shallow_water, Shallow_tracer and Introduction, for the web book (utils.live_figure).
The figures of shallow_demos and shallow_water.py, with the controls of the notebook cells.
"""
from exact_solvers import shallow_water
from exact_solvers.shallow_demos import compare_curves, connect_states, plot_int_curves
from utils.live_figure import InteractiveFigure, TimeFigure, checkbox, radio, slider

HUGONIOT_LOCI = InteractiveFigure.redraw(          # y_axis ('hu' or 'u') given by each cell
    shallow_water.plot_hugoniot_loci,
    [checkbox('plot_1', True, 'Plot 1-loci'), checkbox('plot_2', False, 'Plot 2-loci')])
INTEGRAL_CURVES = InteractiveFigure.redraw(
    plot_int_curves,
    [checkbox('plot_1', True, '1-wave curves'), checkbox('plot_2', False, '2-wave curves')])
COMPARE_CURVES = InteractiveFigure.redraw(
    compare_curves,
    [radio('wave_family', [1, 2], 1, label='Wave family:'),
     slider('h0', 0.1, 3., 1., label='$h_*$'), slider('u0', -3., 3., 0., label='$u_*$'),
     radio('y_axis', ['u', 'hu'], 'u', label='Vertical axis:')])
CONNECT_STATES = InteractiveFigure.redraw(
    connect_states,
    [slider('h_l', 0.001, 2., 1.), slider('u_l', -5., 5., -1.),
     slider('h_r', 0.001, 2., 1.), slider('u_r', -5., 5., 1.)],
    [['h_l', 'h_r'], ['u_l', 'u_r']])                 # left state | right state

# The Introduction: shallow_water.make_demo_plot_function(h_l, h_r, u_l, u_r) with a time slider
DEMO = InteractiveFigure.redraw(
    shallow_water.make_demo_plot_function, [slider('t', 0., 0.6, 0.)],
    factory=True, fixed=dict(fig=0))


def exact_riemann_solution_plot(h_l=3., u_l=0., h_r=1., u_r=0., t=0.2, fig=0):
    """plot_exact_riemann_solution of the chapter's last cell."""
    plot_function = shallow_water.make_demo_plot_function(h_l, h_r, u_l, u_r, hlim=(0, 6), ulim=(-3, 3))
    plot_function(t, fig)


def _draw_exact_riemann_solution(fig, h_l=3., u_l=0., h_r=1., u_r=0., t=0.2):
    plot_function = shallow_water.make_demo_plot_function(h_l, h_r, u_l, u_r, hlim=(0, 6), ulim=(-3, 3))
    return plot_function.draw(fig, t)


# moving t only redraws what depends on it (utils.live_figure.TimeFigure)
exact_riemann_solution_plot.live_figure = lambda: TimeFigure(_draw_exact_riemann_solution, (10, 3))


EXACT_RIEMANN_SOLUTION = InteractiveFigure.redraw(
    exact_riemann_solution_plot,
    [slider('h_l', 0., 5., 3., label='$h_l$'), slider('u_l', -2.5, 2.5, 0., label='$u_l$'),
     slider('h_r', 0., 5., 1., label='$h_r$'), slider('u_r', -2.5, 2.5, 0., label='$u_r$'),
     slider('t', 0., 0.6, 0.)],
    [['h_l', 'h_r'], ['u_l', 'u_r'], ['t']], fixed=dict(fig=0))     # left state | right state


# shallow_water.plot_riemann_SW(...) shows two figures: the solution with a time slider, and
# the x-t plane and phase plane with checkboxes for the characteristics.
def riemann_sw_stripes(h_l, h_r, u_l, u_r, g=1., force_waves=None, extra_lines=None, tracer=False):
    return shallow_water.make_plot_functions(h_l, h_r, u_l, u_r, g, force_waves, extra_lines,
                                             stripes=not tracer, include_contact=tracer)[0]


def riemann_sw_xt_phase(h_l, h_r, u_l, u_r, g=1., force_waves=None, extra_lines=None, tracer=False):
    return shallow_water.make_plot_functions(h_l, h_r, u_l, u_r, g, force_waves, extra_lines,
                                             stripes=not tracer, include_contact=tracer)[1]


CHARACTERISTICS = [checkbox('plot_1_chars', False, '1-characteristics'),
                   checkbox('plot_2_chars', False, '2-characteristics')]
RIEMANN_SW = InteractiveFigure.redraw(
    riemann_sw_stripes, [slider('t', 0., 0.5, 0.)], factory=True, fixed=dict(fig=0))
RIEMANN_SW_PATHS = InteractiveFigure.redraw(            # particle_paths=True (the default)
    riemann_sw_xt_phase, CHARACTERISTICS + [checkbox('plot_tracer_chars', False, 'Particle paths')],
    factory=True)
RIEMANN_SW_TRACER = InteractiveFigure.redraw(           # tracer=True
    riemann_sw_xt_phase, CHARACTERISTICS + [checkbox('plot_tracer_chars', False, 'Tracer characteristics')],
    factory=True)
RIEMANN_SW_CHARACTERISTICS = InteractiveFigure.redraw(  # particle_paths=False
    riemann_sw_xt_phase, CHARACTERISTICS, factory=True,
    fixed=dict(plot_tracer_chars=False))
