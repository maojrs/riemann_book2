"""Write the book's notebooks as plain Jupyter notebooks, with only what is needed to run them:
the `notebooks` branch and the release download (.github/workflows/release.yml).

    python3 .agents/tools/clean_notebooks.py DIR

DIR gets: chapters/ (the chapters of myst.yml, cleaned), figures/ (only the files they use),
exact_solvers/, utils/, miniclaw/, a pyproject.toml for these packages, a README.md and the
licenses. The cleaning only changes markup (code cells are copied as they are):
- the web edition's cells and settings go: {anywidget} cells, frontmatter;
- MyST markup becomes plain Jupyter markdown: {math} blocks -> $$...$$; numbered equations get
  their number as \\tag{n} (as the web book numbers them: the n-th unstarred equation or align
  of the chapter), and {eq}`label` -> (n); citations -> (Author, year) linked to the work;
  heading labels -> links to the heading (to the web book for the home page's); {image} -> <img>;
  {div} wrappers removed; {tip} -> a quoted "Tip:".
Any other MyST markup stops the script, so that none is shipped raw.
"""
import json
import pathlib
import re
import shutil
import sys
import tomllib
from urllib.parse import quote

from bibliography import link, parse_bib, short_citation

ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGES = ('exact_solvers', 'utils', 'miniclaw')
LICENSES = ('LICENSE-CODE', 'LICENSE-TEXT.md')
WEB_BOOK = 'https://maojrs.github.io/riemann_book2/'
LEFTOVER_MARKUP = [r'```\{', r':::\{', r'\{eq\}`', r'\{cite', r'\[@', r'^\([\w:.-]+\)=\s*$',
                   r'\\label\{', r'^:\w+:']


def chapters():
    """The chapters of the table of contents (myst.yml), in order."""
    return re.findall(r'file: (chapters/\S+\.(?:ipynb|md))', (ROOT / 'myst.yml').read_text())


def text(cell):
    """A cell's source as one string (git's nbstripout filter stores it as a list of lines)."""
    return cell['source'] if isinstance(cell['source'], str) else ''.join(cell['source'])


def markdown_cells(path):
    """The notebook (dict) and its markdown sources; a .md file is one markdown cell."""
    if path.endswith('.md'):
        return None, [(ROOT / path).read_text()]
    nb = json.loads((ROOT / path).read_text())
    return nb, [text(c) for c in nb['cells'] if c['cell_type'] == 'markdown']


def anchor(heading):
    """Jupyter's anchor of a heading: its text with spaces as '-'."""
    return '-'.join(heading.split())


def heading_labels(paths):
    """{label: (file name, heading text)} of the (label)= lines before headings."""
    labels = {}
    for path in paths:
        for source in markdown_cells(path)[1]:
            for m in re.finditer(r'^\(([\w:.-]+)\)=\s*\n#+\s+(.+?)\s*$', source, re.M):
                labels[m.group(1)] = (pathlib.Path(path).name, m.group(2))
    return labels


def math_block(m):
    """A ```{math} block (all are unnumbered) as plain display math."""
    body = re.sub(r'^:enumerated: false\n', '', m.group(1)).strip()
    body = re.sub(r'\\(begin|end)\{(equation|align)\}', r'\\\1{\2*}', body)   # unnumbered
    if re.fullmatch(r'\\begin\{(\w+\*?)\}.*\\end\{\1\}', body, re.S):
        return '\n' + body + '\n'                     # an environment: as it is
    return '\n$$\n' + body + '\n$$\n'


def image_block(m):
    """An ```{image} block as centred HTML."""
    width = re.search(r'^:width:\s*(\d+)px', m.group(2), re.M)
    size = f' width="{width.group(1)}"' if width else ''
    return f'<p align="center"><img src="{m.group(1)}"{size}></p>\n'      # blank line: end of the HTML


def number_equations(sources):
    """Number the unstarred equation and align environments in order, as MyST does: each
    becomes starred with \\tag{n} (in place of its \\label, or at its end). Returns the new
    sources and {label: n}."""
    numbers, count, out = {}, 0, []

    def numbered(m):
        nonlocal count
        count += 1
        env, body = m.group(1), m.group(2)
        label = re.search(r'\\label\{([^}]+)\}', body)
        if label:
            numbers[label.group(1)] = count
            body = body.replace(label.group(0), f'\\tag{{{count}}}')
        else:
            body = body.rstrip() + f' \\tag{{{count}}}\n'
        return f'\\begin{{{env}*}}{body}\\end{{{env}*}}'

    for source in sources:
        out.append(re.sub(r'\\begin\{(equation|align)\}(.*?)\\end\{\1\}', numbered, source, flags=re.S))
    return out, numbers


def citations(text, bib):
    """[@a; @b] and {cite:p}`a` -> ([A, year](link); [B, year](link))."""
    def cite(keys):
        works = []
        for key in keys:
            address = link(bib[key]).replace('(', '%28').replace(')', '%29')
            works.append(f'[{short_citation(bib[key])}]({address})')
        return '(' + '; '.join(works) + ')'
    text = re.sub(r'\[(@[^\]]+)\]', lambda m: cite(re.findall(r'@([^\s;\]]+)', m.group(1))), text)
    return re.sub(r'\{cite:p\}`([^`]+)`', lambda m: cite([m.group(1)]), text)


def clean_markdown(sources, name, labels, bib):
    """The markdown of one chapter (in order), cleaned (see the module docstring)."""
    out = []
    for i, source in enumerate(sources):
        if i == 0:
            source = re.sub(r'\A---\n.*?\n---\n?', '', source, flags=re.S)     # frontmatter
        source = re.sub(r'```\{anywidget\}[^\n]*\n.*?```\n?', '', source, flags=re.S)
        source = re.sub(r'```\{math\}\n(.*?)```', math_block, source, flags=re.S)
        source = re.sub(r'```\{image\}\s+(\S+)\n(.*?)```', image_block, source, flags=re.S)
        source = re.sub(r':::\{div\}\n(?::\w+:[^\n]*\n)*(.*?)\n:::', r'\1', source, flags=re.S)
        source = re.sub(r':::\{tip\}\n(.*?)\n:::',
                        lambda m: '> **Tip:** ' + m.group(1).replace('\n', '\n> '), source, flags=re.S)
        out.append(source)
    out, numbers = number_equations(out)
    result = []
    for source in out:
        source = re.sub(r'\{eq\}`([^`]+)`', lambda m: f'({numbers[m.group(1)]})', source)
        source = re.sub(r'\[%s\]\(#([^)]+)\)', lambda m: str(numbers[m.group(1)]), source)

        def heading_link(m):
            file, heading = labels[m.group(2)]
            if file == 'index.md':                   # the home page: only in the web book
                return f'[{m.group(1)}]({WEB_BOOK}#{m.group(2)})'
            target = '' if file == name else file
            return f'[{m.group(1)}]({target}#{quote(anchor(heading), safe="-:")})'
        source = re.sub(r'\[([^\]]*)\]\(#([\w:.-]+)\)', heading_link, source)
        source = re.sub(r'^\([\w:.-]+\)=\s*\n', '', source, flags=re.M)
        source = citations(source, bib)
        for pattern in LEFTOVER_MARKUP:
            m = re.search(pattern, source, re.M)
            if m:
                sys.exit(f'{name}: MyST markup not converted: {source[max(0, m.start() - 60):m.end() + 60]!r}')
        result.append(source)
    return result


def pyproject():
    """pyproject.toml for the three packages, with the book's dependencies."""
    project = tomllib.loads((ROOT / 'pyproject.toml').read_text())['project']
    dependencies = ''.join(f'    "{d}",\n' for d in project['dependencies'])
    packages = ', '.join(f'"{p}"' for p in PACKAGES)
    return f"""[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{project['name']}"
version = "{project['version']}"
description = "{project['description']}"
requires-python = ">=3.10"
dependencies = [
{dependencies}]

[tool.hatch.build.targets.wheel]
packages = [{packages}]
"""


README = f"""# Riemann Problems and Jupyter Solutions: notebooks

The notebooks of the book *Riemann Problems and Jupyter Solutions* (D. I. Ketcheson,
R. J. LeVeque and M. J. del Razo; SIAM, 2020), with the code they need to run. The book, with
interactive figures that run in the browser, is at {WEB_BOOK}.

## Run the notebooks

With Python 3.10 or newer, in this folder:

```bash
pip install -e . jupyterlab
jupyter lab chapters/
```

Or open a chapter on [Binder](https://mybinder.org) from the rocket icon at the top right of
its page in the web book.

## License

The text is licensed under [CC BY-NC-ND 4.0](LICENSE-TEXT.md) and the code under the
[BSD 3-Clause license](LICENSE-CODE).
"""


def write(out):
    """Write the cleaned set into the folder `out` (made empty first)."""
    out = pathlib.Path(out)
    if out.exists():
        shutil.rmtree(out)
    paths = chapters()
    labels = heading_labels(paths + ['index.md'])
    bib = parse_bib((ROOT / 'chapters/references.bib').read_text())
    used = set()
    for path in paths:
        target = out / path
        target.parent.mkdir(parents=True, exist_ok=True)
        nb, sources = markdown_cells(path)
        cleaned = iter(clean_markdown(sources, pathlib.Path(path).name, labels, bib))
        if nb is None:
            content = next(cleaned)
            target.write_text(content)
        else:
            cells = []
            for cell in nb['cells']:
                if cell['cell_type'] == 'markdown':
                    cell = {**cell, 'source': next(cleaned)}
                    if not cell['source'].strip():           # an {anywidget} cell
                        continue
                cells.append(cell)
            nb = {**nb, 'cells': cells}
            content = json.dumps(nb, indent=1, ensure_ascii=False)
            target.write_text(content + '\n')
        used |= set(re.findall(r'\.\./(figures/[\w./-]*\w)', content))
    for figure in sorted(used):
        (out / figure).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / figure, out / figure)
    for package in PACKAGES:
        shutil.copytree(ROOT / package, out / package, ignore=shutil.ignore_patterns('__pycache__'))
    for name in LICENSES:
        shutil.copy2(ROOT / name, out / name)
    (out / 'pyproject.toml').write_text(pyproject())
    (out / 'README.md').write_text(README)


if __name__ == '__main__':
    write(sys.argv[1])
