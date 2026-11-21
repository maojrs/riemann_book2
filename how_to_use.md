---
title: How to use this book
downloads: []
---

<!-- DRAFT: new text for the web edition, to be reviewed and approved by the authors. -->

## Interactive figures

The interactive figures are computed by Python running in your own web browser, on your
computer. There is nothing to install and no account to create, and nothing is sent to a server.

When a chapter opens, Python starts in the background. The first time, your browser downloads
about 20 MB (it keeps them for later visits), and starting takes a few seconds. Until Python is
ready, each figure shows a still picture with the line *This figure becomes interactive when
Python starts in your browser*; the controls appear when it is ready. Each chapter starts its
own Python, so opening another chapter takes a few seconds again.

## Using the figures

- Move the sliders, tick the boxes or choose from the menus, and the figure is drawn again.
- Some figures can be explored by dragging points, such as the left and right states in a
  phase plane, or the time in the $x$-$t$ plane.
- Animations have their own controls to play, pause and step through the frames.
- The figures also work on phones and tablets, more slowly.

If a figure does not respond, wait until its controls appear, or reload the page. If a figure
cannot be drawn for the values you chose, it says so; choose other values.

## The code

The code cells shown in each chapter are the code of its Jupyter notebook. On this site you can
read them, and the figures run them for you. To run or change the code yourself, run the
notebooks in Jupyter, remotely or on your computer:

- **Remotely:** the rocket icon at the top right of a chapter opens it on
  [Binder](https://mybinder.org), where you can run and change its code in JupyterLab. It takes
  longer to load (a few minutes the first time). Binder does not keep your changes: to keep a
  notebook, download it from JupyterLab (*File → Download*).
- **Locally:** [download the notebooks](https://github.com/maojrs/riemann_book2/releases/latest/download/riemann_book_notebooks.zip)
  (with the code they need), unpack them and, in their folder, install the book's code and
  JupyterLab and open the chapters:
  <!-- TODO (before release): the download of this working repository's latest release; change
  it if the official repository is elsewhere. -->

  ```bash
  pip install -e . jupyterlab
  jupyter lab chapters/
  ```
