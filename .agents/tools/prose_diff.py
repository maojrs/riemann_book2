"""Word-level comparison of the prose of two notebooks, ignoring markup (math, citations,
equation references, link targets). Use it to show that a conversion changed no wording:

    python .agents/tools/prose_diff.py ORIGINAL.ipynb chapters/NAME.ipynb

The original notebooks are in clawpack/riemann_book (master).
"""
import json, re, sys, difflib

def prose(path):
    words = []
    for c in json.load(open(path))['cells']:
        if c['cell_type'] != 'markdown': continue
        s = ''.join(c['source'])
        s = re.sub(r'```\{math\}.*?```', ' ', s, flags=re.S)                  # math directives
        s = re.sub(r'```\{image\}.*?```', ' ', s, flags=re.S)
        s = re.sub(r'```\{anywidget\}.*?```', ' ', s, flags=re.S)             # interactive figures
        s = re.sub(r'^\([\w:.-]+\)=$', ' ', s, flags=re.M)                       # heading labels
        s = re.sub(r'\\begin\{(\w+\*?)\}.*?\\end\{\1\}', ' ', s, flags=re.S)  # LaTeX environments
        s = re.sub(r'\$\$.*?\$\$', ' ', s, flags=re.S)
        s = re.sub(r'\$[^$]*\$', ' MATH ', s)                                # inline math
        s = re.sub(r'\(\\ref\{[^}]+\}\)|\{eq\}`[^`]+`|\\eqref\{[^}]+\}', ' EQREF ', s)
        s = re.sub(r'<cite data-cite="([^"]+)">.*?</cite>|\[@([^\]]+)\]', ' CITE ', s, flags=re.S)
        s = re.sub(r'\]\([^)]*\)', ']', s)                                    # link targets
        words += re.findall(r"[A-Za-z0-9'’\-]+|[.,;:!?()]", s)
    return words

a, b = prose(sys.argv[1]), prose(sys.argv[2])
diff = [d for d in difflib.ndiff(a, b) if d[0] in '+-']
print(f"words: {len(a)} original, {len(b)} converted; differences: {len(diff)}")
for d in diff[:40]: print('  ', d)
