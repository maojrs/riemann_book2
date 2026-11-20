"""What the web book's interactive figures ask Python for, in the browser (Pyodide).

Every function takes plain values and returns plain values (numbers, lists, dicts, bytes),
which the page receives as JavaScript objects.
"""
import importlib
import json

import numpy as np

from exact_solvers import acoustics


def _find(path):
    """The object at a dotted path, such as 'exact_solvers.acoustics_demos.DECOMPOSE_Q'."""
    module_name, name = path.rsplit('.', 1)
    return getattr(importlib.import_module(module_name), name)


def warm_up():
    """Imports the plotting code (matplotlib.pyplot, about 3 s in the browser) as soon as
    the page opens, before the first figure needs it."""
    import matplotlib.pyplot  # noqa: F401


# --- Interactive figures (utils.live_figure.InteractiveFigure) -------------------------
_live_figures = {}


def figure_controls(figure):
    """The controls of an InteractiveFigure and how they are laid out."""
    spec = _find(figure)
    return {'controls': spec.controls, 'rows': spec.rows, 'options': spec.options}


def figure_frame(figure, values, setup=None):
    """Pixels of an InteractiveFigure with the given control values: {'width', 'height',
    'rgba'}. Each figure is built once per setup and then only redrawn where it changes."""
    key = json.dumps([figure, setup], sort_keys=True)
    if key not in _live_figures:
        _live_figures[key] = _find(figure).build(setup)
    live = _live_figures[key]
    live.update(**values)
    return live.frame()


# --- Acoustics phase-plane explorer -------------------------------------------------------
def acoustics_explorer(ql, qr, rho, bulk, t=1.0, xmin=-5.0, xmax=5.0, pmin=-5.0, pmax=5.0, n=801):
    """The acoustics Riemann solution for the drag explorer.

    Returns the states q_l, q_m, q_r, the wave speeds -c and c, p(x, t) and u(x, t) at n
    points of [xmin, xmax], and the lines u = u_0 -/+ (p - p_0)/Z through q_l and q_r, in
    the directions of the eigenvectors r1 = (-Z, 1) and r2 = (Z, 1), for p in [pmin, pmax].
    The lines that form the solution (r1 through q_l, r2 through q_r) are marked physical.
    """
    ql, qr = np.asarray(ql, float), np.asarray(qr, float)
    states, speeds, reval = acoustics.exact_riemann_solution(ql, qr, [rho, bulk])
    x = np.linspace(xmin, xmax, n)
    p, u = reval(x/t)
    Z = np.sqrt(rho*bulk)
    pp = np.array([pmin, pmax])

    def line(q, family):
        sign = -1 if family == 1 else 1
        return {'p': pp.tolist(), 'u': (q[1] + sign*(pp - q[0])/Z).tolist()}

    lines = [dict(line(ql, 1), physical=True), dict(line(qr, 2), physical=True),
             dict(line(ql, 2), physical=False), dict(line(qr, 1), physical=False)]
    return {'states': states.T.tolist(), 'speeds': speeds.tolist(),
            'x': x.tolist(), 'p': np.asarray(p).tolist(), 'u': np.asarray(u).tolist(), 'lines': lines}


# --- Shallow water phase-plane explorer ---------------------------------------------------
def shallow_water_explorer(ql, qr, t=2., g=1., hmax=10., xmax=10., n=801):
    """The shallow water Riemann solution for the drag explorer; ql, qr = (h, hu).

    Returns the states q_l, q_m, q_r, the wave types and speeds (a rarefaction has the speeds
    of its edges), h(x, t) and hu(x, t) at n points of [-xmax, xmax], and in the h-hu plane the
    curves through q_l (1-waves) and q_r (2-waves): integral curves (rarefactions) and Hugoniot
    loci (shocks). As in shallow_water.phase_plane_curves, the rarefaction curve below the
    state and the shock curve above it are the physical ones.
    """
    from exact_solvers import shallow_water

    ql, qr = np.asarray(ql, float), np.asarray(qr, float)
    states, speeds, reval, wave_types = shallow_water.exact_riemann_solution(ql, qr, g)
    x = np.linspace(-xmax, xmax, n)
    h, hu = reval(x/t)
    curves = []
    for (h0, hu0), family in ((ql, 1), (qr, 2)):
        below, above = np.linspace(0., h0, 200), np.linspace(h0, hmax, 200)
        for kind, curve, physical, unphysical in (
                ('rarefaction', shallow_water.integral_curve, below, above),
                ('shock', shallow_water.hugoniot_locus, above, below)):
            for hs, is_physical in ((physical, True), (unphysical, False)):
                curves.append({'h': hs.tolist(), 'hu': curve(hs, h0, hu0, family, g, y_axis='hu').tolist(),
                               'kind': kind, 'family': family, 'physical': is_physical})
    return {'states': states.T.tolist(), 'wave_types': list(wave_types),
            'speeds': [np.atleast_1d(s).astype(float).tolist() for s in speeds],
            'x': x.tolist(), 'h': np.asarray(h).tolist(), 'hu': np.asarray(hu).tolist(), 'curves': curves}
