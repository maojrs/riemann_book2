"""What the web book's interactive figures ask Python for, in the browser (Pyodide).

Every function takes plain values and returns plain values (numbers, lists, dicts, bytes),
which the page receives as JavaScript objects. matplotlib is only loaded by the functions
that draw.
"""
import base64
import importlib
import io
import json
import warnings

import numpy as np

from exact_solvers import acoustics


def _find(path):
    """The object at a dotted path, such as 'exact_solvers.acoustics_demos.DECOMPOSE_Q'."""
    module_name, name = path.rsplit('.', 1)
    return getattr(importlib.import_module(module_name), name)


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
        _live_figures[key] = _find(figure).figure(**(setup or {}))
    live = _live_figures[key]
    live.update(**values)
    return live.frame()


# --- Any plotting function (slower: the whole figure is drawn each time) ----------------
_figures = {}


def render_figure(function, values, dpi=100):
    """Call one of the book's plotting functions and return its figure as a PNG data URL,
    cropped as Jupyter shows it. Figures already drawn are remembered."""
    import matplotlib.pyplot as plt

    key = json.dumps([function, values, dpi], sort_keys=True)
    if key not in _figures:
        plt.close('all')
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='FigureCanvasAgg is non-interactive')
            _find(function)(**values)
        buffer = io.BytesIO()
        plt.gcf().savefig(buffer, format='png', dpi=dpi, bbox_inches='tight')
        plt.close('all')
        _figures[key] = 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode()
    return _figures[key]


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
