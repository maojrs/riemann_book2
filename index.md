---
title: Riemann Problems and Jupyter Solutions
downloads: []
---

```{tip}
New to this web edition? See [How to use this book](how_to_use.md): the interactive figures,
and how to run the notebooks yourself.
```

This book illustrates the solution of Riemann problems for hyperbolic partial differential
equations, and the approximate Riemann solvers used in finite volume methods, through
interactive Jupyter notebooks.

Parts I and II are published by SIAM as a print book and an ebook:

> D. I. Ketcheson, R. J. LeVeque and M. J. del Razo,
> [*Riemann Problems and Jupyter Solutions: Theory and Approximate Solvers for Hyperbolic
> PDEs*](https://epubs.siam.org/doi/book/10.1137/1.9781611976212), SIAM, 2020.
> ISBN 978-1-611976-20-5.

The chapters under *Further topics* are additional notebooks on more advanced topics and
additional hyperbolic systems.

## About this web edition

This new release makes the book available as a web edition. Its text, 
scientific content, and underlying scientific code—including the exact 
Riemann solvers and numerical methods—remain unchanged from the original 
edition. The plotting routines and interactive figures, however, have 
been partially rewritten and optimized to run smoothly and efficiently 
in a web browser.

- **Interactive figures in your browser.** The book's own Python code runs in your web browser,
  with no installation, server or account. The plotting was rewritten so that the figures
  respond quickly as you move the sliders, and some figures can be explored by dragging points.
  Python takes a few seconds to start when a chapter opens.
- **Pure Python.** The finite volume computations that the original notebooks did with Clawpack
  use a small Python reimplementation of just the algorithms the book needs. It is not a
  substitute for Clawpack, which does much more.
- **Tested.** A test suite checks the science: exact solutions, jump and entropy conditions,
  conservation, convergence, and agreement with the original book's results.

The original notebooks are available at
[github.com/clawpack/riemann_book](https://github.com/clawpack/riemann_book), and the changes
made in this edition are listed in
[CHANGES.md](https://github.com/maojrs/riemann_book2/blob/main/CHANGES.md).

## License

The text is released under the
[CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/) license, and the code under
the [BSD 3-Clause](https://opensource.org/licenses/BSD-3-Clause) license.
