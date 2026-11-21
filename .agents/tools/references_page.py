"""Write references.md: every work of references.bib, as a plain list
(alphabetical by first author, then year) whose titles link to the works (DOI or URL).

Run from the repository root after changing references.bib or the citations:
    python3 .agents/tools/references_page.py
tests/test_book_pages.py checks that the page lists every entry with its link.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]

ACCENTS = {'"u': 'ü', '"U': 'Ü', '"a': 'ä', '"o': 'ö', "'e": 'é', '`e': 'è'}

HEADER = """---
downloads: []
---

# References

<!-- DRAFT: new page for the web edition, to be reviewed and approved by the authors. -->

The works cited in this book, and related reading. Each title links to the work itself,
through its DOI where it has one.

<!-- Generated from references.bib by .agents/tools/references_page.py: do not edit by hand. -->

"""


def latex_to_text(value):
    """BibTeX text as plain text: accents, escaped characters, braces, page ranges."""
    value = re.sub(r'\{?\\([\'"`][a-zA-Z])\}?', lambda m: ACCENTS.get(m.group(1), m.group(1)[1]), value)
    value = value.replace(r'\&', '&').replace(r'\#', '#').replace('{', '').replace('}', '')
    return re.sub(r'\s+', ' ', value.replace('--', '–')).strip()


def braced(text, start):
    """The text between the brace at text[start] and its matching closing brace."""
    depth = 0
    for i in range(start, len(text)):
        depth += {'{': 1, '}': -1}.get(text[i], 0)
        if depth == 0:
            return text[start + 1:i]
    raise ValueError('unbalanced braces')


def parse_bib(text):
    """{key: {field: value}} for every entry; field names in lower case."""
    entries = {}
    for m in re.finditer(r'@(\w+)\s*\{\s*([^,\s]+),', text):
        body = braced(text, text.index('{', m.start()))
        fields = {'type': m.group(1).lower()}
        for f in re.finditer(r'(\w+)\s*=\s*', body[body.index(',') + 1:]):
            pos = body.index(',') + 1 + f.end()
            if body[pos] == '{':
                value = braced(body, pos)
            elif body[pos] == '"':
                value = body[pos + 1:body.index('"', pos + 1)]
            else:
                value = re.match(r'[^,\s}]+', body[pos:]).group(0)
            fields.setdefault(f.group(1).lower(), value)
        entries[m.group(2)] = fields
    return entries


def initials(given):
    """'Randall J' or 'JM' -> 'R. J.' / 'J. M.'; 'P.-A.' -> 'P.-A.'; 'Bram van' -> 'B. van'."""
    parts = []
    for word in re.sub(r'\.(?=\w)', '. ', given).split():
        if '-' in word:                          # hyphenated: Pierre-Arnaud or P.-A.
            parts.append('-'.join(w.strip('.')[0] + '.' for w in word.split('-') if w.strip('.')))
        elif word.islower():                     # particle (van, de)
            parts.append(word)
        elif word.rstrip('.').isupper() and len(word.rstrip('.')) <= 3:   # initials: JM, J.
            parts.extend(c + '.' for c in word.rstrip('.'))
        else:
            parts.append(word[0] + '.')
    return ' '.join(parts)


def author_list(authors):
    """'Last, First and First Last and ...' -> 'Last, F., Last, F. & Last, F.'"""
    names = []
    for name in re.split(r'\s+and\s+', latex_to_text(authors)):
        if name == 'others':
            continue
        if ',' in name:
            last, given = (s.strip() for s in name.split(',', 1))
        else:
            *given, last = name.split()
            given = ' '.join(given)
        names.append(f'{last}, {initials(given)}' if given else last)
    return names[0] if len(names) == 1 else ', '.join(names[:-1]) + ' & ' + names[-1]


def sort_key(fields):
    last = re.split(r'\s+and\s+', latex_to_text(fields['author']))[0]
    last = last.split(',')[0] if ',' in last else last.split()[-1]
    return (last.lower().replace('ü', 'u').replace('ö', 'o'), fields.get('year', ''))


def link(fields):
    """The work's address: its DOI, through the Handle resolver (MyST turns doi.org links into
    citations), or else its URL. < and > (in some DOIs) are escaped for the markdown link."""
    address = 'https://hdl.handle.net/' + fields['doi'] if 'doi' in fields else fields['url']
    return address.replace('<', '%3C').replace('>', '%3E')


def reference(fields):
    """One reference in markdown, its title a link to the work."""
    link_ = link(fields)
    title = latex_to_text(fields['title']).rstrip('.')
    book = fields['type'] == 'book'
    text = f"{author_list(fields['author'])} ({fields['year']}). "
    text += f"[{'*' + title + '*' if book else title}](<{link_}>)."
    if 'journal' in fields:
        text += f" *{latex_to_text(fields['journal'])}*"
        if 'volume' in fields:
            text += f", {latex_to_text(fields['volume'])}"
            if 'number' in fields:
                text += f"({latex_to_text(fields['number']).lstrip('0')})"
        if 'pages' in fields:
            text += f", {latex_to_text(fields['pages'])}"
        text += '.'
    elif 'publisher' in fields:
        text += ' ' + latex_to_text(fields['publisher']).rstrip(',.') + '.'
    return text


def page():
    works = sorted(parse_bib((ROOT / 'references.bib').read_text()).values(), key=sort_key)
    return HEADER + ''.join(f'1. {reference(fields)}\n' for fields in works)


if __name__ == '__main__':
    (ROOT / 'references.md').write_text(page())
