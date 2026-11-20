"""Every interactive cell of the chapters and its web version (the {anywidget} cell after it).

The chapter's code cells are run in order with ipywidgets' interact replaced by a recorder,
which builds the same controls (ipywidgets.interactive) without showing them. Each web figure
must then have the notebook's controls (names, ranges, values, labels) laid out as in the
notebook, its fixed arguments, and draw the same picture.
"""
import builtins
import io
import itertools
import json
import pathlib
import re
import sys
import types
import warnings

import matplotlib

matplotlib.use('Agg')

import IPython.display  # noqa: E402
import ipywidgets  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402
from PIL import Image  # noqa: E402

from utils.live_figure import InteractiveFigure  # noqa: E402
from widgets.compute import _find  # noqa: E402

CHAPTERS = pathlib.Path(__file__).resolve().parent.parent / 'chapters'
WIDGET = re.compile(r'```\{anywidget\} \.\./widgets/interact\.mjs\n:css: [^\n]*\n(\{.*\})\n```', re.S)
SLOW = ('_animation(',)          # cells not needed here (miniclaw animations)


def source(cell):
    return cell['source'] if isinstance(cell['source'], str) else ''.join(cell['source'])


def chapters_with_widgets():
    return sorted(p.stem for p in CHAPTERS.glob('*.ipynb') if 'widgets/interact.mjs' in p.read_text())


def run_chapter(name, monkeypatch):
    """Run the code cells; return {code cell index: [recorded interactive figures]} and the
    web models {code cell index: [models of the widget cells after it]}. An interact figure
    is recorded as (ipywidgets.interactive, the layout its function displays or None)."""
    recorded, models, current = {}, {}, []
    patched = {'interact': ipywidgets.interact, 'display': IPython.display.display}

    def interact(f, **kwargs):
        figure = ipywidgets.interactive(f, **kwargs)
        current.append(['interact', (figure, None)])
        return types.SimpleNamespace(widget=figure)        # as interact: f.widget
    interact.recorder = True

    def display(*objects, **kwargs):          # a function's own layout of its interact controls,
        for obj in objects:                     # or the image a plotting function shows
            if isinstance(obj, ipywidgets.Box):
                current[-1][1] = (current[-1][1][0], obj)
            elif isinstance(obj, IPython.display.Image):
                shown.append(obj.data)
    display.recorder = True
    recorders = {'interact': interact, 'display': display}

    def interactive_figure(spec, setup=None, widgets=None, **values):
        if widgets:                                      # values given through the widgets
            values = {name: w.value for name, w in widgets.items()}
        current.append(('InteractiveFigure', (spec, setup or {}, values)))

    monkeypatch.setattr(ipywidgets, 'interact', interact)
    monkeypatch.setattr(IPython.display, 'display', display)
    monkeypatch.setattr(builtins, 'display', display, raising=False)    # as in IPython
    monkeypatch.setattr(InteractiveFigure, 'interact', interactive_figure)
    monkeypatch.chdir(CHAPTERS)
    namespace = {}
    cells = json.loads((CHAPTERS / f'{name}.ipynb').read_text())['cells']
    last_code = None
    for i, cell in enumerate(cells):
        text = source(cell)
        if cell['cell_type'] == 'markdown':
            m = WIDGET.search(text)
            if m:
                models.setdefault(last_code, []).append(json.loads(m.group(1)))
            continue
        last_code = i
        if any(s in text for s in SLOW):
            continue
        for module in list(sys.modules.values()):      # modules imported before the patch,
            for name, recorder in recorders.items():     # or during an earlier test
                bound = getattr(module, name, None)
                if bound is patched[name] or getattr(bound, 'recorder', False):
                    monkeypatch.setattr(module, name, recorder)
        current.clear()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            exec(compile(text, f'{name}[{i}]', 'exec'), namespace)
        recorded[i] = [tuple(r) for r in current]
        plt.close('all')
    return recorded, models


shown = []        # images shown with display() by the plotting functions


def plain(x):
    """x with numpy arrays and numbers as lists and floats, to compare with the JSON of a cell."""
    return json.loads(json.dumps(x, default=lambda a: np.asarray(a).tolist()))


def png_pixels(png):
    return np.asarray(Image.open(io.BytesIO(png)).convert('RGBA')).astype(int)


def notebook_picture(figure):
    """The interact figure as Jupyter shows it, with its initial control values: the image
    its function shows, or else its pyplot figure."""
    plt.close('all')
    shown.clear()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        figure.f(**figure.kwargs)
    if shown:
        return png_pixels(shown[-1])
    buffer = io.BytesIO()
    plt.gcf().savefig(buffer, format='png', bbox_inches='tight')
    plt.close('all')
    return png_pixels(buffer.getvalue())


def check_controls(spec, values, figure):
    """The web controls are the notebook's: same names, kinds, ranges, labels and values."""
    widgets = {w._kwarg: w for w in figure.kwargs_widgets if not isinstance(w, ipywidgets.fixed)}
    controls = {c['name']: c for c in spec.controls}
    assert set(controls) == set(widgets)
    for name, w in widgets.items():
        c = controls[name]
        assert values[name] == pytest.approx(w.value) if isinstance(w.value, float) else values[name] == w.value, name
        assert c['label'] == w.description, name
        if isinstance(w, ipywidgets.FloatSlider):
            assert c['kind'] == 'slider'
            assert (c['min'], c['max'], c['step']) == pytest.approx((w.min, w.max, w.step)), name
        elif isinstance(w, ipywidgets.Checkbox):
            assert c['kind'] == 'checkbox'
        elif isinstance(w, (ipywidgets.Dropdown, ipywidgets.RadioButtons)):
            kind = 'radio' if isinstance(w, ipywidgets.RadioButtons) else 'dropdown'
            assert c['kind'] == kind and tuple(c['options']) == tuple(w.options), name
        else:
            raise AssertionError(f'{name}: {type(w).__name__} is not handled by the web figures')


def original_rows(figure, layout):
    """The notebook's controls, by name, row by row: the function's own layout (rows of
    HBoxes in a VBox, or an HBox of controls and VBox columns; None where a column has no
    control), or else interact's, one per line."""
    if layout is None:
        return [[w._kwarg] for w in figure.kwargs_widgets if not isinstance(w, ipywidgets.fixed)]
    lines = [[w._kwarg for w in box.children] if isinstance(box, ipywidgets.Box) else [box._kwarg]
             for box in layout.children]
    if isinstance(layout, ipywidgets.VBox):
        return lines
    return [list(row) for row in itertools.zip_longest(*lines)]


def check_fixed(spec, setup, figure):
    """The cell's fixed() arguments are given to the web figure too."""
    given = {**spec.fixed, **setup}
    for w in figure.kwargs_widgets:
        if isinstance(w, ipywidgets.fixed):
            assert w._kwarg in given and given[w._kwarg] == w.value, w._kwarg


@pytest.mark.parametrize('name', chapters_with_widgets())
def test_web_figures_match_the_notebook(name, monkeypatch):
    recorded, models = run_chapter(name, monkeypatch)
    assert models, 'no widget cells'
    for cell, cell_models in models.items():
        assert len(cell_models) == len(recorded[cell]), f'cell {cell}: widget cells and interact calls'
        for model, (kind, record) in zip(cell_models, recorded[cell]):
            spec, setup = _find(model['figure']), model.get('setup', {})
            values = spec.initial_values(**model.get('values', {}))
            if kind == 'InteractiveFigure':                  # the cell already uses the same figure
                notebook_spec, notebook_setup, notebook_values = record
                assert notebook_spec is spec and plain(notebook_setup) == plain(setup)
                assert plain(spec.initial_values(**notebook_values)) == plain(values)
                continue
            figure, layout = record
            check_controls(spec, values, figure)
            assert (spec.rows, spec.options) == (original_rows(figure, layout), []), \
                f'cell {cell} {model["figure"]}: controls laid out as in the notebook'
            check_fixed(spec, setup, figure)
            web = spec.build(setup)
            web.update(**values)
            web_pixels = png_pixels(web.png())
            notebook = notebook_picture(figure)
            assert web_pixels.shape == notebook.shape, f'cell {cell} {model["figure"]}'
            differing = (np.abs(web_pixels - notebook).max(axis=2) > 40).mean()
            assert differing < 0.002, f'cell {cell} {model["figure"]}: {100*differing:.2f}% of the pixels differ'
            plt.close('all')
