"""Convert an original riemann_book notebook (in chapters/) to the MyST conventions of
.agents/conversion.md. Only markup changes: the wording of the text is never touched.

    uv run python .agents/tools/convert_notebook.py chapters/Acoustics.ipynb

Prints every kind of change it made, and anything it could not convert safely
(to be fixed by hand and reported to the user).
"""

import json
import re
import sys
from collections import Counter

BIB_KEYS = set(re.findall(r'^@\w+\s*\{([^,]+),', open('references.bib').read(), re.M))

changes, warnings = Counter(), []


def unnumbered_math(body):
    """An unnumbered display equation (align* or $$...$$ in the original)."""
    return f"\n```{{math}}\n:enumerated: false\n{body.strip()}\n```\n"


def top_level_rows(body):
    """Split the body of an align environment at its top-level \\\\ (not inside cases,
    matrices or other nested environments)."""
    rows, depth, start, i = [], 0, 0, 0
    while i < len(body):
        if body.startswith('\\begin{', i):
            depth += 1
        elif body.startswith('\\end{', i):
            depth -= 1
        elif body.startswith('\\\\', i) and depth == 0:
            rows.append(body[start:i])
            start = i + 2
            i += 2
            continue
        i += 1
    rows.append(body[start:])
    return [r for r in rows if r.strip()]


def split_labels(src):
    """MyST gives a math block one label (and one number), so an align with several
    \\label{} becomes one align per labelled row (rows without a label stay with the next
    labelled row). The LaTeX of each row is unchanged."""
    def split(m):
        env, body = m.group(1), m.group(2)
        if len(re.findall(r'\\label\{', body)) < 2:
            return m.group(0)
        blocks, pending = [], []
        for row in top_level_rows(body):
            pending.append(row)
            labels = re.findall(r'\\label\{[^}]+\}', row)
            if labels:
                rows = [re.sub(r'\s*\\label\{[^}]+\}', '', r).strip() for r in pending]
                blocks.append(f"\\begin{{{env}}}\n    " + ' \\\\\n    '.join(rows) + f" {labels[0]}\n\\end{{{env}}}")
                pending = []
        if pending:
            warnings.append('rows without a label after the last label kept in a separate block')
            blocks.append(f"\\begin{{{env}}}\n    " + ' \\\\\n    '.join(r.strip() for r in pending) + f"\n\\end{{{env}}}")
        changes['equations with several labels split'] += 1
        return '\n\n'.join(blocks)
    return re.sub(r'\\begin\{(align|equation)\}(.*?)\\end\{\1\}', split, src, flags=re.S)


def remove_top_level(body, token):
    """body without `token` where it is not inside a nested environment."""
    out, depth, i = [], 0, 0
    while i < len(body):
        if body.startswith('\\begin{', i):
            depth += 1
        elif body.startswith('\\end{', i):
            depth -= 1
        if depth == 0 and body.startswith(token, i) and not body.startswith('\\' + token, i - 1):
            i += len(token)
            continue
        out.append(body[i])
        i += 1
    return ''.join(out)


def unalign_single_rows(src):
    """A one-row align with at most one top-level & becomes an equation (align* becomes plain
    display math): it looks the same, but KaTeX can then break it after an = when it is
    wider than the screen, instead of scrolling. The alignment & is the only thing removed."""
    def single(m):
        env, star, body = m.group(1), m.group(2), m.group(3)
        if len(top_level_rows(body)) != 1 or body.rstrip().endswith('\\\\'):
            return m.group(0)
        top_amps = body.count('&') - remove_top_level(body, '&').count('&')
        if top_amps > 1:
            return m.group(0)
        changes['one-row align -> equation'] += 1
        inner = remove_top_level(body, '&')
        return unnumbered_math(inner) if star else f"\\begin{{equation}}{inner}\\end{{equation}}"
    return re.sub(r'\\begin\{(align)(\*?)\}(.*?)\\end\{align\2\}', single, src, flags=re.S)


def convert_markdown(src, cell_index):
    src = unalign_single_rows(split_labels(src))
    # Equation references: (\ref{X}) and \eqref{X} render as "(n)", which {eq} also does.
    src, n = re.subn(r'\(\\ref\{([^}]+)\}\)', r'{eq}`\1`', src)
    changes['equation references'] += n
    src, n = re.subn(r'\\eqref\{([^}]+)\}', r'{eq}`\1`', src)
    changes['equation references'] += n
    for bare in re.findall(r'\\ref\{([^}]+)\}', src):
        warnings.append(f"cell {cell_index}: bare \\ref{{{bare}}} left unchanged (renders without parentheses)")

    # Citations (cite2c): <cite data-cite="key"><a href="...">(text)</a></cite> -> [@key]
    def cite(m):
        key = m.group(1)
        if key not in BIB_KEYS:
            warnings.append(f"cell {cell_index}: citation key {key!r} not in references.bib")
        changes['citations'] += 1
        return f'[@{key}]'
    src = re.sub(r'<cite data-cite="([^"]+)">.*?</cite>', cite, src, flags=re.S)
    for link in re.findall(r'\]\(\w+\.ipynb#[^)]+\)', src):
        warnings.append(f"cell {cell_index}: link to a heading {link}: give the heading a label (name)= and link to #name")
    for link in re.findall(r'\]\([^)]*riemann(?:_bib)?\.html#[^)]*\)', src):
        warnings.append(f"cell {cell_index}: bibliography link left unchanged: {link}")

    # Unnumbered display math: align*, equation*, gather* and $$...$$
    def star(m):
        changes['unnumbered equations'] += 1
        return unnumbered_math(m.group(0))
    src = re.sub(r'\\begin\{(align|equation|gather)\*\}.*?\\end\{\1\*\}', star, src, flags=re.S)

    def dollars(m):
        changes['unnumbered equations'] += 1
        return unnumbered_math(m.group(1))
    src = re.sub(r'\$\$(.+?)\$\$', dollars, src, flags=re.S)

    # Paths relative to chapters/
    src, n = re.subn(r'\]\((?:\./)?(figures/|exact_solvers/|utils/)', r'](../\1', src)
    changes['relative paths'] += n
    src, n = re.subn(r'src="(?:\./)?(figures/)', r'src="../\1', src)
    changes['relative paths'] += n
    return src


def image_cell(code):
    """Image('figures/x.png', width=N) -> an {image} block, or None."""
    m = re.fullmatch(r"\s*Image\(['\"]([^'\"]+)['\"](?:\s*,\s*width\s*=\s*(\d+))?\s*\)\s*", code)
    if not m:
        return None
    width = f"\n:width: {m.group(2)}px" if m.group(2) else ""
    return f"```{{image}} ../{m.group(1)}{width}\n:align: center\n```"


def convert_code(src, cell_index, seen_imports):
    lines = [l for l in src.split('\n') if not re.match(r'\s*%(matplotlib|config)\b', l)]
    if len(lines) != len(src.split('\n')):
        changes['notebook magics removed'] += 1
    src = '\n'.join(lines).strip('\n')

    # Phase-plane HTML: IFrame(src='phase_plane/X.html', ...) -> embedded HTML (IFrames to
    # local files are not copied into the site).
    def iframe(m):
        changes['phase-plane IFrame -> embedded HTML'] += 1
        return f"HTML(open('../figures/phase_plane/{m.group(1)}').read())"
    src = re.sub(r"IFrame\(\s*src\s*=\s*['\"]phase_plane/([^'\"]+)['\"][^)]*\)", iframe, src, flags=re.S)
    if re.search(r'IFrame\(', src):
        warnings.append(f"cell {cell_index}: IFrame left unchanged")
    src = re.sub(r"(['\"])(figures/)", r"\1../\2", src)

    # Import cells that only repeat names imported earlier
    statements = [l.strip() for l in src.split('\n') if l.strip()]
    if statements and all(re.match(r'(import|from)\s', s) for s in statements):
        names = set()
        for s in statements:
            m = re.match(r'from\s+(\S+)\s+import\s+(.+)', s)
            if m:
                names |= {(m.group(1), n.strip()) for n in m.group(2).split(',')}
            else:
                names |= {('', n.strip()) for n in s[len('import'):].split(',')}
        if names <= seen_imports:
            changes['duplicate import cells removed'] += 1
            return None
        seen_imports.update(names)
    return src


def add_html_import(cells):
    """The embedded phase-plane HTML needs HTML: add it to the IPython.display import."""
    for cell in cells:
        if cell['cell_type'] != 'code':
            continue
        lines = cell['source'].split('\n')
        for k, line in enumerate(lines):
            m = re.match(r'from IPython\.display import (.+)$', line.strip())
            if m:
                if 'HTML' not in [n.strip() for n in m.group(1).split(',')]:
                    lines[k] = line.rstrip() + ', HTML'
                    cell['source'] = '\n'.join(lines)
                    changes['HTML added to the IPython.display import'] += 1
                return
    warnings.append('no IPython.display import found: add HTML for the embedded phase planes')


def convert(path):
    nb = json.load(open(path))
    cells, seen_imports = [], set()
    for i, cell in enumerate(nb['cells']):
        src = ''.join(cell['source'])
        if cell['cell_type'] == 'markdown':
            cell['source'] = convert_markdown(src, i)
        elif cell['cell_type'] == 'code':
            image = image_cell(src.replace('\n', ''))
            if image is not None:
                changes['Image() cells -> {image}'] += 1
                cells.append({'cell_type': 'markdown', 'metadata': {}, 'source': image})
                continue
            new = convert_code(src, i, seen_imports)
            if new is None or not new.strip():
                continue
            cell['source'] = new
        cells.append(cell)
    if changes['phase-plane IFrame -> embedded HTML']:
        add_html_import(cells)
    nb['cells'] = cells
    with open(path, 'w') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
        f.write('\n')


if __name__ == '__main__':
    for path in sys.argv[1:]:
        changes.clear(); warnings.clear()
        convert(path)
        print(path)
        for what, n in changes.items():
            print(f"  {what}: {n}")
        for w in warnings:
            print(f"  WARNING {w}")
