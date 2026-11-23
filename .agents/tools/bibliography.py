"""Reading chapters/references.bib: entries, author names and links, for the pages and notebooks made
from it (references_page.py, clean_notebooks.py)."""
import re

ACCENTS = {'"u': 'ü', '"U': 'Ü', '"a': 'ä', '"o': 'ö', "'e": 'é', '`e': 'è'}


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


def surnames_of(fields):
    """The authors' surnames, in order ('others' left out)."""
    names = []
    for name in re.split(r'\s+and\s+', latex_to_text(fields['author'])):
        if name != 'others':
            names.append(name.split(',')[0].strip() if ',' in name else name.split()[-1])
    return names


def sort_key(fields):
    """Alphabetical by first author's surname, then year."""
    last = surnames_of(fields)[0]
    return (last.lower().replace('ü', 'u').replace('ö', 'o'), fields.get('year', ''))


def link(fields, resolver='https://doi.org/'):
    """The work's address: its DOI through `resolver`, or else its URL. < and > (in some DOIs)
    are escaped for a markdown link."""
    address = resolver + fields['doi'] if 'doi' in fields else fields['url']
    return address.replace('<', '%3C').replace('>', '%3E')


def short_citation(fields):
    """The author-year citation: 'LeVeque, 2002', 'Lighthill & Whitham, 1955',
    'Del Razo et al., 2016' (as the web book shows it)."""
    surnames = surnames_of(fields)
    names = surnames[0] if len(surnames) == 1 else ' & '.join(surnames) if len(surnames) == 2 \
        else surnames[0] + ' et al.'
    return f"{names}, {fields['year']}"
