"""Write references.md: every work of references.bib, as a plain list
(alphabetical by first author, then year) whose titles link to the works (DOI or URL).

Run from the repository root after changing references.bib or the citations:
    python3 .agents/tools/references_page.py
tests/test_book_pages.py checks that the page lists every entry with its link.
"""
import pathlib

from bibliography import author_list, latex_to_text, link, parse_bib, sort_key

ROOT = pathlib.Path(__file__).resolve().parents[2]

# MyST turns doi.org links into citations: the page links DOIs through the Handle resolver
RESOLVER = 'https://hdl.handle.net/'

HEADER = """---
downloads: []
---

# References

<!-- DRAFT: new page for the web edition, to be reviewed and approved by the authors. -->

The works cited in this book, and related reading. Each title links to the work itself,
through its DOI where it has one.

<!-- Generated from references.bib by .agents/tools/references_page.py: do not edit by hand. -->

"""



def reference(fields):
    """One reference in markdown, its title a link to the work."""
    link_ = link(fields, RESOLVER)
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
