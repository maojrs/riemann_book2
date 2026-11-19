# Notebook conversion conventions (from jbook2test)

Rule 1 in AGENTS.md applies: only markup changes, never the wording.

- `\begin{align}\label{X}` becomes a `{math}` block with `:label: X`. `\ref{X}` or `(\ref{X})` becomes `` {eq}`X` ``. Unlabelled `align` becomes `align*`.
- Links to `riemann_bib.html#key` become `[@key]` citations.
- Links between notebooks (e.g. `[Euler](Euler.ipynb)`) become MyST cross-references; the link text stays the same.
- `Image(...)` becomes `{image}` or `{figure}`. Phase-plane HTML becomes an `{iframe}` or a component.
- Remove `%matplotlib inline`, `%config` and duplicated imports. Hide demo-only code cells with `remove-input` or `hide-input` tags.
