"""The book's pages: each chapter's header links to its own notebook on Binder."""
import json
import pathlib
import re
from urllib.parse import quote

ROOT = pathlib.Path(__file__).resolve().parents[1]
BINDER = 'https://mybinder.org/v2/gh/maojrs/riemann_book2/notebooks?labpath='   # the cleaned notebooks (release.yml)


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


def bibliography():
    """references.bib: {key: entry text}."""
    text = (ROOT / 'chapters/references.bib').read_text()
    return dict(re.findall(r'@\w+\s*\{\s*([^,\s]+),(.*?)(?=\n@|\Z)', text, re.S))


def cited_keys():
    """The keys cited in the chapters ([@key], [@a; @b] or {cite:p}`key`)."""
    keys = set()
    for path in ROOT.glob('chapters/*'):
        if path.suffix == '.ipynb':
            cells = json.loads(path.read_text())['cells']
            text = ''.join(c['source'] if isinstance(c['source'], str) else ''.join(c['source']) for c in cells)
        else:
            text = path.read_text()
        for group in re.findall(r'\[(@[^\]]+)\]', text):
            keys |= set(re.findall(r'@([^\s;\]]+)', group))
        keys |= set(re.findall(r'\{cite:p\}`([^`]+)`', text))
    return keys


def link(entry):
    """The References page's link to a bibliography entry: its DOI through the Handle resolver
    (doi.org links become citations in MyST), else its URL; < and > escaped."""
    doi = re.search(r'^\s*doi\s*=\s*\{(\S+)\}', entry, re.M | re.I)
    address = 'https://hdl.handle.net/' + doi.group(1) if doi else \
        re.search(r'^\s*url\s*=\s*\{(\S+)\}', entry, re.M | re.I).group(1)
    return address.replace('<', '%3C').replace('>', '%3E')


def test_every_reference_links_to_the_work():
    """Every entry has a DOI or, for works without one, a URL; every cited key exists."""
    entries = bibliography()
    for key, entry in entries.items():
        assert re.search(r'^\s*(doi|url)\s*=\s*\{\S+\}', entry, re.M | re.I), key
    assert cited_keys() <= set(entries)


def test_references_page_lists_every_work():
    """chapters/references.md (made by .agents/tools/references_page.py): one item per entry of
    references.bib (every cited work and related reading), its title linked to the work."""
    page = (ROOT / 'chapters/references.md').read_text()
    items = re.findall(r'^1\. .*\]\(<(\S+)>\)', page, re.M)
    assert sorted(items) == sorted(link(entry) for entry in bibliography().values())
    assert 'file: chapters/references.md' in (ROOT / 'myst.yml').read_text()


def test_how_to_use_is_on_the_home_page():
    """"How to use this book" is a subsection of the home page's "About this web edition"."""
    toc = re.findall(r'- file: (\S+)', (ROOT / 'myst.yml').read_text())
    assert toc[:2] == ['index.md', 'chapters/Preface.md']
    assert not (ROOT / 'how_to_use.md').exists()
    page = (ROOT / 'index.md').read_text()
    about = page.index('## About this web edition')
    assert about < page.index('### How to use this book') < page.index('## License')
    assert '(how-to-use)=\n### How to use this book' in page
    assert '](#how-to-use)' in (ROOT / 'chapters/Preface.md').read_text()
    assert 'releases/latest/download/riemann_book_notebooks.zip' in page
    assert 'rocket icon' in page and 'pip install -e . jupyterlab' in page


def test_every_figure_used_by_a_chapter_exists_and_svgs_have_sources():
    """Every image a chapter shows is in figures/; each SVG diagram has its TikZ source and
    is made by figures/src/build.sh (white background with a margin, readable on the dark theme)."""
    build = (ROOT / 'figures/src/build.sh').read_text()
    used = set()
    for path in chapters() + ['chapters/Preface.md']:
        used |= set(re.findall(r'\.\./figures/([\w/.-]+\.(?:png|svg|jpg))', (ROOT / path).read_text()))
    assert 'acoustics_xt_plane.svg' in used
    for name in used:
        assert (ROOT / 'figures' / name).exists(), name
        if name.endswith('.svg'):
            assert (ROOT / 'figures/src' / name.replace('.svg', '.tex')).exists(), name
            assert name[:-4] in build, name
