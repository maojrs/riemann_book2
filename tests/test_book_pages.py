"""The book's pages: each chapter's header links to its own notebook on Binder."""
import json
import pathlib
import re
from urllib.parse import quote

ROOT = pathlib.Path(__file__).resolve().parents[1]
BINDER = 'https://mybinder.org/v2/gh/maojrs/riemann_book2/main?labpath='


def chapters():
    """The notebooks of the table of contents (myst.yml), in order (the Preface is markdown)."""
    return re.findall(r'file: (chapters/\S+\.ipynb)', (ROOT / 'myst.yml').read_text())


def frontmatter(path):
    """The YAML block at the start of the notebook's first cell, as text ('' if none)."""
    cell = json.loads((ROOT / path).read_text())['cells'][0]
    source = cell['source'] if isinstance(cell['source'], str) else ''.join(cell['source'])
    block = re.match(r'---\n(.*?)\n---(\n|$)', source, re.S)
    return block.group(1) if block else ''


def test_every_chapter_opens_its_own_notebook_on_binder():
    assert len(chapters()) == 21
    for path in chapters():
        assert re.search(r'^edit_url: (\S+)$', frontmatter(path), re.M).group(1) == \
            BINDER + quote(path, safe=''), path


def test_no_other_edit_link_and_no_downloads():
    """No edit link on pages without a Binder link; no download menu on any page (a page
    without its own downloads gets its source file as one)."""
    assert re.search(r'^  edit_url: null$', (ROOT / 'myst.yml').read_text(), re.M)
    for path in chapters():
        assert re.search(r'^downloads: \[\]$', frontmatter(path), re.M), path
    for page in ('index.md', 'chapters/Preface.md'):
        assert re.search(r'^---\n(.*\n)*?downloads: \[\]\n(.*\n)*?---', (ROOT / page).read_text()), page


def test_binder_installs_the_books_code_from_pyproject():
    """Binder (repo2docker) has no configuration of its own here: it installs pyproject.toml in
    place (`pip install -e .`), on its default Python, 3.10, which the project must allow."""
    assert not (ROOT / '.binder').exists() and not (ROOT / 'binder').exists()
    assert re.search(r'^requires-python = ">=3\.10"$', (ROOT / 'pyproject.toml').read_text(), re.M)
