import javabridge
import matplotlib
matplotlib.use("module://backend_swing")
import matplotlib.figure
import backend_swing
import numpy as np
import threading
import matplotlib.pyplot as plt

def popup_script_dlg(canvas):
    joptionpane = javabridge.JClassWrapper("javax.swing.JOptionPane")
    jresult = joptionpane.showInputDialog(
        "Enter a script command")
    if jresult is not None:
        result = javabridge.to_string(jresult)
        axes = canvas.figure.axes[0]
        eval(result, globals(), locals())
        canvas.draw()
    
def run_ui():
    figure = plt.figure()
    ax = figure.add_axes([.05, .05, .9, .9])
    x = np.linspace(0, np.pi * 8)
    ax.plot(x, np.sin(x))
    canvas = figure.canvas
    frame = canvas.component.getTopLevelAncestor()
    toolbar = plt.get_current_fig_manager().frame.toolbar
    toolbar.add_button(lambda event:popup_script_dlg(canvas), "hand")
    plt.show()
    return frame, canvas, toolbar

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
frame, canvas, toolbar = run_ui()
frame.addWindowListener(adapter)
frame.setVisible(True)
event.wait()
javabridge.kill_vm()
