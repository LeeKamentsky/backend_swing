# backend_swing
A Java/swing backend for Matplotlib using the javabridge

Many of the Python UI toolkits - wx, qt and similar, have a matplotlib backend that displays plots on screen using the
toolkit. Now that the python-javabridge is bidirectional, we have all the pieces we need to use AWT and Swing as a Python
toolkit, arguably the most complete, platform-independent one there is. It turns out that, with agg, it's not hard to
do, so here it is.

Currently, very early in development - can only display figures.

# How to use
First install matplotlib and the javabridge (if you have not done so already; on Linux, you might have to install
`libpng12-dev` and `libfreetype6-dev` first):

```sh
pip install --user matplotlib
pip install --user git+https://github.com/CellProfiler/python-javabridge
```

Then you can run the demo:

```sh
PYTHONPATH=. python demo/canvas_demo.py
```
