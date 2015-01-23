import javabridge
import matplotlib
import matplotlib.figure
import backend_swing
import numpy as np
import threading

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
    frame = javabridge.JClassWrapper('javax.swing.JFrame')()
    figure = matplotlib.figure.Figure()
    ax = figure.add_axes([.05, .05, .9, .9])
    x = np.linspace(0, np.pi * 8)
    ax.plot(x, np.sin(x))
    canvas = backend_swing.FigureCanvasSwing(figure)
    def on_key(event, canvas = canvas):
        print "Received key %s" % repr(event)
        if event.key == "Enter":
            popup_script_dlg(canvas)
    def on_release(event):
        if event.x is None or event.y is None or event.inaxes is None:
            print "Mouse button released outside of axis"
            return
        print "Mouse button released: button=%d, x=%f, y=%f, xdata=%f, ydata=%f" % (
            event.button, event.x, event.y, event.xdata, event.ydata)
    def on_move(event):
        if event.x is None or event.y is None or event.inaxes is None:
            return
        print "Mouse moved: x=%f, y=%f, xdata=%f, ydata=%f" % (
            event.x, event.y, event.xdata, event.ydata)
        
    canvas.mpl_connect('key_press_event', on_key)
    canvas.mpl_connect('button_release_event', on_release)
    canvas.mpl_connect('motion_notify_event', on_move)
    center = javabridge.get_static_field('java/awt/BorderLayout', 'CENTER',
                                         'Ljava/lang/String;')
    javabridge.call(frame.o, "add", "(Ljava/awt/Component;Ljava/lang/Object;)V", canvas.component.o, center)
    toolbar = backend_swing.NavigationToolbar2Swing(canvas, frame)
    toolbar.add_button(lambda event:popup_script_dlg(canvas), "hand")
    frame.pack()
    frame.setVisible(True)
    frame.setSize(640, 480)
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
event.wait()
javabridge.kill_vm()
