"""widgets.compute: what the web book's interactive figures ask Python for."""

import json
import subprocess
import sys

import matplotlib

matplotlib.use('Agg')

import numpy as np  # noqa: E402
import pytest  # noqa: E402

from exact_solvers import acoustics, acoustics_demos  # noqa: E402
from widgets import compute  # noqa: E402

PHASE_PLANE = 'exact_solvers.acoustics_demos.PHASE_PLANE'


def test_figure_controls_describe_the_notebook_controls():
    spec = compute.figure_controls(PHASE_PLANE)
    json.dumps(spec)                                              # sent to the page as JSON
    assert spec['rows'] == [['pl', 'ul', 'rho'], ['pr', 'ur', 'bulk']]
    assert spec['options'] == ['xmin', 'xmax', 'ymin', 'ymax']
    names = [c['name'] for c in spec['controls']]
    assert names == [c['name'] for c in acoustics_demos.PHASE_PLANE.controls]


def test_warm_up_imports_the_plotting_code():
    """In a fresh Python (as in the browser): compute does not import pyplot, warm_up does."""
    code = ("import sys; from widgets import compute; "
            "assert 'matplotlib.pyplot' not in sys.modules; "
            "assert compute.warm_up() is None; "
            "assert 'matplotlib.pyplot' in sys.modules")
    subprocess.run([sys.executable, '-c', code], check=True)


def test_figure_frame_is_the_live_figure():
    values = dict(pl=3., ul=2., pr=3., ur=-2., rho=0.5, bulk=2., xmin=1e-7, xmax=10., ymin=-5., ymax=5.)
    frame = compute.figure_frame(PHASE_PLANE, values)
    assert len(frame['rgba']) == 4*frame['width']*frame['height']
    live = acoustics_demos.PhasePlane()
    live.update(**values)
    assert frame == live.frame()


def test_figure_frame_builds_one_figure_per_setup():
    figure = 'exact_solvers.acoustics_demos.RIEMANN_PLOT_PPLANE'
    shock_tube = dict(ql=[5, 0], qr=[1, 0], rho=1., bulk=4.)
    wall = dict(ql=[2, 1], qr=[2, -1], rho=1., bulk=1.5)
    a = compute.figure_frame(figure, dict(t=0.5, which_char=None), shock_tube)
    b = compute.figure_frame(figure, dict(t=0.5, which_char=None), wall)
    assert a['rgba'] != b['rgba']
    assert compute.figure_frame(figure, dict(t=0.5, which_char=None), shock_tube) == a


def test_acoustics_explorer_is_the_exact_solution():
    ql, qr, rho, bulk = [-2, 2], [0, -3], 1., 4.
    data = compute.acoustics_explorer(ql, qr, rho, bulk, t=1.)
    json.dumps(data)
    states, speeds, reval = acoustics.exact_riemann_solution(np.array(ql, float), np.array(qr, float), [rho, bulk])
    np.testing.assert_allclose(data['states'], states.T)
    np.testing.assert_allclose(data['states'][1], [4., -1.])      # q_m of the book's figure
    np.testing.assert_allclose(data['speeds'], [-2., 2.])
    x = np.array(data['x'])
    np.testing.assert_allclose(data['p'], reval(x)[0])
    np.testing.assert_allclose(data['u'], reval(x)[1])
    # The solution lines meet at q_m; each line has slope -/+ 1/Z
    Z = np.sqrt(rho*bulk)
    for line, slope in zip(data['lines'][:2], [-1/Z, 1/Z]):
        p, u = np.array(line['p']), np.array(line['u'])
        assert (u[1] - u[0])/(p[1] - p[0]) == slope
        assert np.interp(4., p, u) == -1.
    assert [line['physical'] for line in data['lines']] == [True, True, False, False]


def test_browser_and_assets_use_the_same_pyodide_version():
    """widgets/python.mjs loads Pyodide from the CDN, or the copy made by widgets/assets.py."""
    import pathlib
    import re
    root = pathlib.Path(__file__).resolve().parents[2]
    in_browser = re.search(r"PYODIDE_VERSION = '([\d.]+)'", (root/'widgets'/'python.mjs').read_text()).group(1)
    in_assets = re.search(r"PYODIDE_VERSION = '([\d.]+)'", (root/'widgets'/'assets.py').read_text()).group(1)
    assert in_browser == in_assets


def test_shallow_water_explorer_is_the_exact_solution():
    from exact_solvers import shallow_water
    ql, qr = [3., 5.], [3., -5.]
    data = compute.shallow_water_explorer(ql, qr, t=2.)
    json.dumps(data)
    states, speeds, reval, wave_types = shallow_water.exact_riemann_solution(np.array(ql), np.array(qr), 1.)
    np.testing.assert_allclose(data['states'], states.T)
    assert data['wave_types'] == list(wave_types)
    x = np.array(data['x'])
    np.testing.assert_allclose(data['h'], reval(x/2.)[0])
    np.testing.assert_allclose(data['hu'], reval(x/2.)[1])
    # The physical curves through q_l (1-waves) and q_r (2-waves) meet at q_m
    hm, hum = data['states'][1]
    for family in (1, 2):
        kind = wave_types[0 if family == 1 else 1]
        curve = next(c for c in data['curves'] if c['family'] == family and c['physical']
                     and c['kind'] == ('shock' if kind == 'shock' else 'rarefaction'))
        assert np.interp(hm, curve['h'], curve['hu']) == pytest.approx(hum, abs=1e-3)
