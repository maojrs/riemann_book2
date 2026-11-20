"""The book's plotting functions with a time slider, drawn on live figures
(utils.live_figure.TimeFigure), draw the same picture as the whole-figure pyplot versions
they replaced (tests/reference/plotting_before.py), at every time, also after other times
were shown; and the notebook functions show that figure."""
import io
import os
import sys
import warnings

import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402
from PIL import Image  # noqa: E402

from exact_solvers import burgers, nonconvex_demos, shallow_water, traffic_demos, traffic_LWR  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'reference'))
import plotting_before as before  # noqa: E402

TIMES = (0.1, 0.45, 0.8)
TOLERANCE = 0.005     # pixels: anti-aliased edges (a spine, adjacent stripes) may come out slightly apart


def cases():
    """(name, live figure, its values besides t, the previous function drawing at time t)."""
    return [
        ('burgers.plot_riemann', burgers.plot_riemann.live_figure, dict(q_l=0.5, q_r=0., x_range=1.),
         lambda t: before.plot_riemann(0.5, 0., t, 1.)),
        ('burgers.plot_riemann, shock, wide', burgers.plot_riemann.live_figure,
         dict(q_l=0.2, q_r=0.9, x_range=2.), lambda t: before.plot_riemann(0.2, 0.9, t, 2.)),
        ('traffic_LWR.plot_riemann_traffic', traffic_LWR.plot_riemann_traffic.live_figure,
         dict(rho_l=0.5, rho_r=0., xrange=1.), lambda t: before.plot_riemann_traffic(0.5, 0., t, 1.)),
        ('traffic_demos.jam', traffic_demos.jam.live_figure, dict(rho_l=0.5), lambda t: before.jam(0.5, t)),
        ('traffic_demos.green_light', traffic_demos.green_light.live_figure, dict(rho_r=0.3),
         lambda t: before.green_light(0.3, t)),
        ('nonconvex_demos.make_plot_function',
         nonconvex_demos.make_plot_function(nonconvex_demos.buckley_leverett, 1., 0., -2, 2).live_figure, {},
         lambda t: before.make_plot_function(nonconvex_demos.buckley_leverett, 1., 0., -2, 2)(t)),
        ('nonconvex_demos.make_plot_function_qsliders',
         nonconvex_demos.make_plot_function_qsliders(np.sin).live_figure, dict(q_left=-3.5, q_right=3.5),
         lambda t: before.make_plot_function_qsliders(np.sin)(t, -3.5, 3.5)),
        ('shallow_water.make_demo_plot_function', shallow_water.make_demo_plot_function(3., 1., 0., 0.).live_figure,
         {}, lambda t: before.make_demo_plot_function(3., 1., 0., 0.)(t)),
        ('shallow_water.make_demo_plot_function, stripes of plot_riemann_SW',
         shallow_water.make_plot_functions(2., 2., 1., -1.)[0].live_figure, {},
         lambda t: before.make_demo_plot_function(2., 2., 1., -1., figsize=(7, 2), hlim=(0, 4.5), ulim=(-2, 2))(t)),
        ('shallow_water.make_demo_plot_function, forced rarefaction',
         shallow_water.make_plot_functions(4., 1., 0., 0., force_waves='raref')[0].live_figure, {},
         lambda t: before.make_demo_plot_function(4., 1., 0., 0., figsize=(7, 2), hlim=(0, 4.5), ulim=(-2, 2),
                                                  force_waves='raref')(t)),
    ]


def pixels(png):
    return np.asarray(Image.open(io.BytesIO(png)).convert('RGBA')).astype(int)


def before_picture(draw, t):
    plt.close('all')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        draw(t)
    buffer = io.BytesIO()
    plt.gcf().savefig(buffer, format='png', bbox_inches='tight')
    plt.close('all')
    return pixels(buffer.getvalue())


def differing(a, b):
    assert a.shape == b.shape
    return (np.abs(a - b).max(axis=2) > 40).mean()


@pytest.mark.parametrize('name, live_figure, values, draw_before', cases(), ids=[c[0] for c in cases()])
def test_live_figure_is_the_previous_figure(name, live_figure, values, draw_before):
    figure = live_figure()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        figure.update(t=0.9, **values)                   # built at another time
        figure.png()
        for t in TIMES:
            figure.update(t=t, **values)
            expected = before_picture(draw_before, t)
            assert differing(pixels(figure.png()), expected) < TOLERANCE, t
        assert differing(pixels(figure.png()), before_picture(draw_before, TIMES[0])) > TOLERANCE  # wrong t


def test_euler_stripes_are_the_previous_curves():
    """Euler's plot_with_stripes keeps its axes for all times now and its stripes cover the
    domain (so neither is compared); its curves are those of the previous function."""
    from exact_solvers import euler_demos
    values = dict(rho_l=2., u_l=0., p_l=2.5, rho_r=3., u_r=0., p_r=5., gamma=1.4)
    figure = euler_demos.plot_with_stripes.live_figure()
    figure.update(t=0.9, **values)
    for t in TIMES:
        figure.update(t=t, **values)
        plt.close('all')
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            before.plot_with_stripes(**values, t=t)
        for live, previous in zip(figure.fig.axes, plt.gcf().axes):
            assert np.allclose(live.lines[0].get_ydata(), previous.lines[0].get_ydata(), equal_nan=True)
        plt.close('all')


@pytest.mark.parametrize('values', [
    dict(rho_l=2., u_l=0., p_l=2.5, rho_r=3., u_r=0., p_r=5.),     # the chapter's demo
    dict(rho_l=1., u_l=5., p_l=1., rho_r=1., u_r=-5., p_r=1.),     # inflow from both sides
    dict(rho_l=1., u_l=-2., p_l=1., rho_r=1., u_r=2., p_r=1.),     # outflow
])
def test_euler_stripes_cover_the_domain(values):
    """The tracer stripes fill [-1, 1] at every time, without gaps."""
    from exact_solvers import euler_demos
    figure = euler_demos.plot_with_stripes.live_figure()
    for t in np.linspace(0., 1., 6):
        figure.update(t=t, gamma=1.4, **values)
        extents = sorted((path.vertices[:, 0].min(), path.vertices[:, 0].max())
                         for c in figure.fig.axes[0].collections for path in c.get_paths())
        assert extents[0][0] <= -1 + 1e-9 and extents[-1][1] >= 1 - 1e-9, t
        assert all(b[0] <= a[1] + 1e-9 for a, b in zip(extents, extents[1:])), t


def test_euler_demo_axes_do_not_follow_small_changes():
    """In euler_demo1 every slider only redraws the solution: the vertical ranges stay put
    while the solution fits them and fills a quarter of them."""
    from exact_solvers import euler_demos
    figure = euler_demos.stripes_demo.live_figure()
    values = dict(rho_l=2., u_l=0., p_l=2.5, rho_r=3., u_r=0., p_r=5., gamma=1.4, t=0.5)
    figure.update(**values)
    limits = [ax.get_ylim() for ax in figure.fig.axes]
    for t in (0.1, 0.9):
        figure.update(**{**values, 't': t})
        assert [ax.get_ylim() for ax in figure.fig.axes] == limits
    built = figure.fig
    figure.update(**{**values, 'rho_l': 2.1})
    assert figure.fig is built and len(figure.fig.axes[0].collections) == 1     # one set of stripes
    assert figure.fig.axes[1].get_ylim() == limits[1] and figure.fig.axes[2].get_ylim() == limits[2]


@pytest.mark.parametrize('values', [
    dict(rho_l=2., u_l=0., p_l=2.5, rho_r=3., u_r=0., p_r=5.),     # the chapter's demo
    dict(rho_l=3., u_l=0., p_l=3., rho_r=1., u_r=0., p_r=1.),      # Sod-like
    dict(rho_l=1., u_l=5., p_l=1., rho_r=1., u_r=-5., p_r=1.),     # colliding flows
    dict(rho_l=1., u_l=-2., p_l=1., rho_r=1., u_r=2., p_r=1.),     # strong expansion
    dict(rho_l=10., u_l=0., p_l=10., rho_r=1., u_r=0., p_r=1.),
])
def test_euler_stripes_stay_inside_their_axes(values):
    from exact_solvers import euler_demos
    figure = euler_demos.plot_with_stripes.live_figure()
    for t in np.linspace(0., 1., 11):
        figure.update(t=t, gamma=1.4, **values)
        for ax in figure.fig.axes:
            low, high = ax.get_ylim()
            y = ax.lines[0].get_ydata()
            y = y[np.isfinite(y)]
            assert low < y.min() and y.max() < high, (ax.get_title(), t)


def test_euler_stripes_at_time_zero_are_the_initial_states():
    """At t = 0 the pressure plot shows p_l and p_r (it used to come from a zero energy)."""
    from exact_solvers import euler_demos
    figure = euler_demos.plot_with_stripes.live_figure()
    figure.update(t=0., rho_l=2., u_l=0., p_l=2.5, rho_r=3., u_r=0., p_r=5., gamma=1.4)
    pressure = figure.fig.axes[2].lines[0]
    x, p = pressure.get_xdata(), pressure.get_ydata()
    assert np.allclose(p[x <= 0], 2.5) and np.allclose(p[x > 0], 5.)
