# Copyright 2015 Broad Institute, all rights reserved.

import javabridge
import matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backend_bases import \
     FigureManagerBase, NavigationToolbar2
import numpy as np
import os

class FigureCanvasSwing(FigureCanvasAgg):
    def __init__(self, figure):
        FigureCanvasAgg.__init__(self, figure)
        self.__ref_id, self.__ref = javabridge.create_jref(self)
        self.__cpython = javabridge.make_instance(
            'org/cellprofiler/javabridge/CPython', '()V')

        paint_script = (
            'import javabridge\n'
            'self = javabridge.redeem_jref("%s")\n'
            'self.draw(javabridge.JWrapper(graphics))\n') % self.__ref_id
        
        component = javabridge.run_script("""
        new javax.swing.JComponent() {
            paintComponent: function(graphics) {
                locals = new java.util.Hashtable();
                locals.put("graphics", graphics);
                cpython.exec(script, locals, locals);
            }
        }
        """, dict(cpython = self.__cpython, script = paint_script))
        self.__component = javabridge.JWrapper(component)
        self.__event_queue_class = None
        self.__component_listener = javabridge.JProxy(
            'java.awt.event.ComponentListener',
            dict(componentHidden = self._on_component_hidden,
                 componentMoved = self._on_component_moved,
                 componentResized = self._on_component_resized,
                 componentShown = self._on_component_shown))
        self.__component.addComponentListener(self.__component_listener.o)
        self.__key_event_cls = javabridge.JClassWrapper(
            'java.awt.event.KeyEvent')
        self.__key_listener = javabridge.JProxy(
            'java.awt.event.KeyListener',
            dict(keyPressed=self._on_key_pressed,
                 keyReleased=self._on_key_released,
                 keyTyped=self._on_key_typed))
        self.__component.addKeyListener(self.__key_listener.o)
        self.__component.setFocusable(True)
        self.__mouse_listener = javabridge.JProxy(
            'java.awt.event.MouseListener',
            dict(mouseClicked=self._on_mouse_clicked,
                 mouseEntered=self._on_mouse_entered,
                 mouseExited=self._on_mouse_exited,
                 mousePressed=self._on_mouse_pressed,
                 mouseReleased=self._on_mouse_released))
        self.__component.addMouseListener(self.__mouse_listener.o)
        self.__mouse_motion_listener = javabridge.JProxy(
            'java.awt.event.MouseMotionListener',
            dict(mouseDragged=self._on_mouse_dragged,
                 mouseMoved=self._on_mouse_moved))
        self.__component.addMouseMotionListener(self.__mouse_motion_listener.o)
           
    @property
    def component(self):
        return self.__component
    
    def draw(self, graphics=None):
        '''Render the figure
        
        :param graphics: the AWT Graphics gc that should be used to draw.
                         If None and not in the AWT thread, the call is
                         reflected via EventQueue.invokeAndWait, otherwise
                         a graphics context is created and drawn.
        '''
        FigureCanvasAgg.draw(self)
        self.jimage = _convert_agg_to_awt_image(self.get_renderer(), None)
        self._isDrawn = True
        self.gui_repaint(graphics)
        
    def gui_repaint(self, graphics = None):
        '''Do the actual painting on the Java canvas'''
        if not self._eqc.isDispatchThread():
            self.__component.repaint()
        else:
            if self.__component.isShowing():
                color = javabridge.JClassWrapper(
                    'java.awt.Color')(*self.figure.get_facecolor())
                if graphics is None:
                    graphics = self.__component.getGraphics()
                graphics.drawImage(self.jimage, 0, 0, color, None)

    def blit(self, bbox=None):
        raise NotImplementedError("TODO: implement blit")
    
    def _on_component_hidden(self, event):
        pass
    
    def _on_component_moved(self, event):
        pass
    
    def _on_component_shown(self, event):
        pass
    
    def _get_key(self, event):
        modifiers = javabridge.call(event, "getModifiers", "()I")
        keycode = javabridge.call(event, "getKeyCode", "()I")
        keytext = javabridge.to_string(
            self.__key_event_cls.getKeyText(keycode))
        if modifiers != 0:
            modtext = javabridge.to_string(
                self.__key_event_cls.getKeyModifiersText(modifiers)).lower()
            return "%s+%s" % (modtext, keytext)
        return keytext
    
    def _on_key_pressed(self, event):
        key = self._get_key(event)
        javabridge.call(event, "consume", "()V")
        self.key_press_event(key, guiEvent=event)
        
    def _on_key_released(self, event):
        key = self._get_key(event)
        javabridge.call(event, "consume", "()V")
        self.key_release_event(key, guiEvent=event)
        
    def _on_key_typed(self, event):
        # TODO: determine if we ever get this after consuming
        pass
    
    def _on_mouse_clicked(self, event):
        pass
    
    def _on_mouse_entered(self, event):
        pass
    
    def _on_mouse_exited(self, event):
        pass
    
    def _get_mouse_x_y_button(self, event):
        x = javabridge.call(event, "getX", "()I")
        y = self.figure.bbox.height - javabridge.call(event, "getY", "()I")
        button = javabridge.call(event, "getButton", "()I")
        return x, y, button
    
    def _on_mouse_pressed(self, event):
        x, y, button = self._get_mouse_x_y_button(event)
        javabridge.call(event, "consume", "()V")
        self.button_press_event(x, y, button, guiEvent=event)
    
    def _on_mouse_released(self, event):
        x, y, button = self._get_mouse_x_y_button(event)
        javabridge.call(event, "consume", "()V")
        self.button_release_event(x, y, button, guiEvent=event)
        
    def _on_mouse_dragged(self, event):
        x, y, button = self._get_mouse_x_y_button(event)
        self.motion_notify_event(x, y, guiEvent=event)
        
    def _on_mouse_moved(self, event):
        x, y, button = self._get_mouse_x_y_button(event)
        self.motion_notify_event(x, y, guiEvent=event)
    
    def _on_component_resized(self, event):
        w = float(self.__component.getWidth())
        h = float(self.__component.getHeight())
        if w <= 0 or h <= 0:
            return
        dpival = self.figure.dpi
        winch = w/dpival
        hinch = h/dpival
        self.figure.set_size_inches(winch, hinch)
        self._isDrawn = False
        self.__component.repaint()
        FigureCanvasAgg.resize_event(self)
        
    
    @property
    def _eqc(self):
        '''java.awt.EventQueue.class'''
        if self.__event_queue_class is None:
            self.__event_queue_class = javabridge.JClassWrapper(
                "java.awt.EventQueue")
        return self.__event_queue_class

class NavigationToolbar2Swing(NavigationToolbar2):
    def __init__(self, canvas, frame):
        self._frame = frame
        self._tools = {}
        NavigationToolbar2.__init__(self, canvas)
        self._idle = True
        
    def _init_toolbar(self):
        self.toolbar = javabridge.JClassWrapper('javax.swing.JToolBar')()
        self.toolbar.setFloatable(False)
        self.radio_button_group = javabridge.JClassWrapper(
            'javax.swing.ButtonGroup')()
        for text, tooltip_text, image_file, callback in self.toolitems:
            if text is None:
                self.toolbar.addSeparator()
                continue
            callback = getattr(self, callback, None)
            if callback is None:
                continue
            if text in ("Pan", "Zoom"):
                self.add_radio_button(callback, image_file)
            else:
                self.add_button(callback, image_file)
        north = javabridge.get_static_field('java/awt/BorderLayout', 'NORTH',
                                             'Ljava/lang/String;')
        javabridge.call(self._frame.o, "add", 
                        "(Ljava/awt/Component;Ljava/lang/Object;)V",
                        self.toolbar.o, north)
        
    def make_action(self, action, icon_name):
        basedir = os.path.join(matplotlib.rcParams['datapath'], 'images')
        filename = os.path.normpath(os.path.join(basedir, icon_name+".png"))
        if os.path.exists(filename):
            jfile = javabridge.JClassWrapper('java.io.File')(filename)
            image = javabridge.JClassWrapper('javax.imageio.ImageIO').read(
                jfile)
            icon = javabridge.JClassWrapper('javax.swing.ImageIcon')(image)
        else:
            icon = None
        class ActionListener(javabridge.JProxy):
            def __init__(self, action):
                javabridge.JProxy.__init__(self, 'java.awt.event.ActionListener')
                self.action = action
                
            def actionPerformed(self, event):
                self.action(event)
        action_listener = ActionListener(action)
                
        jaction = javabridge.run_script(
            """var result = new JavaAdapter(javax.swing.AbstractAction,
                                            javax.swing.Action, {
                actionPerformed: function(event) {
                    action_listener.actionPerformed(event);
                }
             });
             result.putValue(javax.swing.Action.NAME, name);
             result.putValue(javax.swing.Action.SMALL_ICON, icon);
             result
             """, dict(action_listener=action_listener.o,
                       name = icon_name,
                       icon = icon.o if icon is not None else icon))
        self._tools[icon_name] = (action_listener, jaction)
        return jaction
        
    def add_radio_button(self, action, icon_name):
        jaction = self.make_action(action, icon_name)
        button = javabridge.JClassWrapper('javax.swing.JToggleButton')(jaction)
        self.toolbar.add(button)
        self.radio_button_group.add(button)
        return button
        
    def add_button(self, action, icon_name):
        jaction = self.make_action(action, icon_name)
        return self.toolbar.add(jaction)
    
def _convert_agg_to_awt_image(renderer, awt_image):
    '''Use the renderer to draw the figure on a java.awt.BufferedImage
    
    :param renderer: the RendererAgg that's in charge of rendering the figure
    
    :param awt_image: a javabridge JB_Object holding the BufferedImage or
                      None to create one.
    
    :returns: the BufferedImage
    '''
    env = javabridge.get_env()
    w = int(renderer.width)
    h = int(renderer.height)
    buf = np.frombuffer(renderer.buffer_rgba(), np.uint8).reshape(w * h, 4)
    cm = javabridge.JClassWrapper('java.awt.image.DirectColorModel')(
        32, int(0x000000FF), int(0x0000FF00), int(0x00FF0000), -16777216)
    raster = cm.createCompatibleWritableRaster(w, h)
    for i in range(4):
        samples = env.make_int_array(buf[:, i].astype(np.int32))
        raster.setSamples(0, 0, w, h, i, samples)
                          
    awt_image = javabridge.JClassWrapper('java.awt.image.BufferedImage')(
        cm, raster, False, None)
    return awt_image
