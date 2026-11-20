"""widgets.compute: what the web book's interactive figures ask Python for."""

import base64
import io
import json

import matplotlib

matplotlib.use('Agg')

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

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


def test_render_figure_draws_any_plotting_function():
    url = compute.render_figure('exact_solvers.acoustics_demos.decompose_q', dict(p=1., u=0.3, K=1., rho=1.))
    assert url.startswith('data:image/png;base64,')
    image = Image.open(io.BytesIO(base64.b64decode(url.split(',')[1])))
    assert image.size[0] > 500                                    # an 8x4 inch figure at 100 dpi, cropped
    assert compute.render_figure('exact_solvers.acoustics_demos.decompose_q',
                                 dict(p=1., u=0.3, K=1., rho=1.)) is url    # remembered


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
    root = pathlib.Path(__file__).resolve().parent.parent
    in_browser = re.search(r"PYODIDE_VERSION = '([\d.]+)'", (root/'widgets'/'python.mjs').read_text()).group(1)
    in_assets = re.search(r"PYODIDE_VERSION = '([\d.]+)'", (root/'widgets'/'assets.py').read_text()).group(1)
    assert in_browser == in_assets
