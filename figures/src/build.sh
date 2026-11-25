#!/bin/sh
# Make the SVG figures from their LaTeX sources (needs LaTeX with TikZ, and dvisvgm).
# Glyphs become paths, so the SVGs need no fonts. The zoom makes the 12pt labels the size of
# the math in the web book (KaTeX: 1.21em). Run from anywhere:
#   sh figures/src/build.sh
set -e
cd "$(dirname "$0")"
out=$(mktemp -d)
for name in shallow_water_riemann nonlinear_elasticity_riemann acoustics_xt_plane; do
  latex -interaction=batchmode -halt-on-error -output-directory="$out" "$name.tex" > /dev/null
  dvisvgm --no-fonts --exact-bbox --optimize --zoom=1.25 --verbosity=1 -o "../$name.svg" "$out/$name.dvi"
done
rm -r "$out"
