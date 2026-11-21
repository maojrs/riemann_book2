---
title: Riemann Problems and Jupyter Solutions
downloads: []
---

<!-- DRAFT: new text for the web edition, to be reviewed and approved by the authors. -->

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

This is a re-release of the book as a web edition. The text, the science and the book's
scientific code (its exact Riemann solvers and numerical methods) remain the same; the plotting
and the interactive figures were rewritten and optimized for display in a web browser:

- **Interactive figures in your browser.** The book's own Python code runs in your web browser,
  with no installation, server or account. The plotting was rewritten so that the figures
  respond quickly as you move the sliders, and some figures can be explored by dragging points.
  Python takes a few seconds to start when a chapter opens.
- **Pure Python.** The finite volume computations that the original notebooks did with Clawpack
  use a small Python reimplementation of just the algorithms the book needs. It is not a
  substitute for Clawpack, which does much more.
- **Tested.** A test suite checks the science: exact solutions, jump and entropy conditions,
  conservation, convergence, and agreement with the original book's results.
- **Run the notebooks yourself.** Each chapter is a Jupyter notebook and can be run locally or
  remotely:
  - **Remotely:** the rocket icon at the top right of a chapter opens it on
    [Binder](https://mybinder.org), where you can run and change its code in JupyterLab. It
    takes longer to load (a few minutes the first time).
  - **Locally:** [download the whole project](#) and run the notebooks in Jupyter on your
    computer.
    <!-- TODO (before release): replace the placeholder link "#" with the download of the
    official repository (e.g. its .zip on GitHub). -->

The original notebooks are available at
[github.com/clawpack/riemann_book](https://github.com/clawpack/riemann_book), and the changes
made in this edition are listed in
[CHANGES.md](https://github.com/maojrs/riemann_book2/blob/main/CHANGES.md).

## License

The text is released under the
[CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/) license, and the code under
the [BSD 3-Clause](https://opensource.org/licenses/BSD-3-Clause) license.
