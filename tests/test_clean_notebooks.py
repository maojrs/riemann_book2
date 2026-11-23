"""The notebooks of the `notebooks` branch and the release download
(.agents/tools/clean_notebooks.py): only what is needed to run them, plain Jupyter markdown,
the web book's equation numbers and links, the code cells as they are."""
import json
import pathlib
import re
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHAPTERS = re.findall(r'file: (chapters/\S+\.(?:ipynb|md))', (ROOT / 'myst.yml').read_text())


@pytest.fixture(scope='module')
def clean(tmp_path_factory):
    out = tmp_path_factory.mktemp('notebooks') / 'set'
    subprocess.run([sys.executable, str(ROOT / '.agents/tools/clean_notebooks.py'), str(out)], check=True)
    return out


def cells(path):
    return json.loads(path.read_text())['cells']


def text(cell):
    """A cell's source as one string (git's nbstripout filter stores it as a list of lines)."""
    return cell['source'] if isinstance(cell['source'], str) else ''.join(cell['source'])


def markdown(path):
    if path.suffix == '.md':
        return path.read_text()
    return '\n'.join(text(c) for c in cells(path) if c['cell_type'] == 'markdown')


def test_only_what_is_needed_to_run_the_notebooks(clean):
    assert sorted(p.name for p in clean.iterdir()) == sorted([
        'chapters', 'figures', 'exact_solvers', 'utils', 'miniclaw', 'pyproject.toml', 'README.md',
        'LICENSE-CODE', 'LICENSE-TEXT.md'])
    assert sorted(str(p.relative_to(clean)) for p in (clean / 'chapters').iterdir()) == sorted(CHAPTERS)
    used = ''.join((clean / c).read_text() for c in CHAPTERS)
    for figure in (clean / 'figures').rglob('*'):
        if figure.is_file():
            assert '../' + str(figure.relative_to(clean)) in used, figure
    assert not list(clean.rglob('__pycache__'))
    packages = re.search(r'^packages = \[(.*)\]$', (clean / 'pyproject.toml').read_text(), re.M).group(1)
    assert packages == '"exact_solvers", "utils", "miniclaw"'


def test_no_web_markup_left(clean):
    for chapter in CHAPTERS:
        text = markdown(clean / chapter)
        for pattern in [r'\{anywidget\}', r'```\{', r':::\{', r'\{eq\}`', r'\{cite', r'\[@',
                        r'^\([\w:.-]+\)=', r'\\label\{', r'^:\w+:', r'\A---\n', 'edit_url', '%s']:
            assert not re.search(pattern, text, re.M), (chapter, pattern)


def test_code_cells_unchanged(clean):
    for chapter in CHAPTERS:
        if chapter.endswith('.ipynb'):
            code = [c for c in cells(ROOT / chapter) if c['cell_type'] == 'code']
            assert [c for c in cells(clean / chapter) if c['cell_type'] == 'code'] == code, chapter


def test_equation_numbers_and_references(clean):
    """Equations are numbered as in the web book (the n-th unstarred equation or align), with
    \\tag{n}; a reference {eq}`label` becomes (n) of the same equation."""
    text = markdown(clean / 'chapters/Acoustics.ipynb')
    assert re.search(r'\\tag\{1\}\s*\\rho_t \+ \(\\rho u\)_x\s*= 0', text)       # Ac:continuity
    assert 'equations (1)-(2) form a hyperbolic system' in text
    for chapter in CHAPTERS:
        tags = [int(n) for n in re.findall(r'\\tag\{(\d+)\}', markdown(clean / chapter))]
        assert tags == list(range(1, len(tags) + 1)), chapter
    assert 'Comparing to equations (1, 2)' in markdown(clean / 'chapters/Euler_Tammann.ipynb')


def test_citations_link_to_the_works(clean):
    text = markdown(clean / 'chapters/Traffic_flow.ipynb')
    assert '([Lighthill & Whitham, 1955](https://doi.org/10.1098/rspa.1955.0089))' in text
    assert '([LeVeque, 2002](http://faculty.washington.edu/rjl/book.html))' in text
    assert '([Lax, 1972](https://doi.org/10.1137/1.9781611970562))' in markdown(clean / 'chapters/Preface.md')


def test_heading_links_point_to_headings(clean):
    """Links to labelled headings point to the heading (Jupyter anchors: spaces as '-')."""
    found = 0
    for chapter in CHAPTERS:
        for target, anchor in re.findall(r'\]\((\w*\.ipynb)?#([^)\s]+)\)', markdown(clean / chapter)):
            page = clean / 'chapters' / target if target else clean / chapter
            headings = re.findall(r'^#+\s+(.+?)\s*$', markdown(page), re.M)
            assert anchor in ['-'.join(h.split()) for h in headings], (chapter, target, anchor)
            found += 1
    assert found >= 9


def test_packages_import(clean):
    code = 'import exact_solvers.acoustics, utils.riemann_tools, miniclaw.pyclaw'
    subprocess.run([sys.executable, '-c', code], cwd=clean, check=True)


def test_preface_tip_links_to_the_web_book(clean):
    """The Preface's tip becomes a quoted "Tip:"; its link to the home page's "How to use this
    book" goes to the web book (the home page is not in the notebooks)."""
    text = markdown(clean / 'chapters/Preface.md')
    assert ('> **Tip:** New to this web edition? See [How to use this book]'
            '(https://maojrs.github.io/riemann_book2/#how-to-use)') in text
