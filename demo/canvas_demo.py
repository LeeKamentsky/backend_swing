import javabridge
import matplotlib
import matplotlib.figure
import backend_swing
import numpy as np
import threading

def run_ui():
    frame = javabridge.JClassWrapper('javax.swing.JFrame')()
    figure = matplotlib.figure.Figure()
    ax = figure.add_axes([.05, .05, .9, .9])
    x = np.linspace(0, np.pi * 8)
    ax.plot(x, np.sin(x))
    canvas = backend_swing.FigureCanvasSwing(figure)
    frame.setContentPane(canvas.component)
    frame.setVisible(True)
    frame.setSize(640, 480)
    return frame, canvas

javabridge.start_vm()
javabridge.activate_awt()
event = threading.Event()
event_ref_id, event_ref = javabridge.create_jref(event)
cpython = javabridge.JClassWrapper('org.cellprofiler.javabridge.CPython')()
set_event_script = (
    'import javabridge\n'
    'event = javabridge.redeem_jref("%s")\n'
    'event.set()') % event_ref_id
adapter = javabridge.run_script("""
new java.awt.event.WindowAdapter() {
    windowClosed: function(e) {
        cpython.exec(script);
    }
}
""", dict(cpython=cpython, script=set_event_script))
frame, canvas = run_ui()
frame.addWindowListener(adapter)
event.wait()
javabridge.kill_vm()
