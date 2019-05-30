import logging
from tkinter import *
from tkinter.ttk import *


mlogger = logging.getLogger('babel_logger')


input_widgets = (
    'Combobox', 'Listbox', 'TButton', 'TEntry', 'TCheckbutton')


def disable_widgets(widgets):
    for w in widgets:
        for s in w.winfo_children():
            if s.winfo_class() in input_widgets:
                s['state'] = DISABLED
        if w.winfo_class() in input_widgets:
            w['state'] = DISABLED


def enable_widgets(widgets):
    for w in widgets:
        for s in w.winfo_children():
            if s.winfo_class() in input_widgets:
                s['state'] = NORMAL
        if w.winfo_class() in input_widgets:
            w['state'] = NORMAL


class BusyManager:
    """cursor manager"""

    def __init__(self, widget):
        self.toplevel = widget.winfo_toplevel()
        self.widgets = {}

    def busy(self, widget=None):
        if widget is None:
            w = self.toplevel
        else:
            w = widget

        if str(w) not in self.widgets:
            try:
                # attach cursor to this widget
                cursor = w.cget("cursor")
                if cursor != "watch":
                    self.widgets[str(w)] = (w, cursor)
                    w.config(cursor="watch")
            except tk.TclError:
                pass

        for w in w.children.values():
            self.busy(w)

    def notbusy(self):
        # restore cursors
        for w, cursor in self.widgets.values():
            try:
                w.config(cursor=cursor)
            except tk.TclError:
                pass
        self.widgets = {}


class ToolTip(object):

    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 27
        y = y + cy + self.widget.winfo_rooty() + 27
        self.tipwindow = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))

        label = Label(
            tw, text=self.text, justify=LEFT,
            background="#ffffe0", relief=SOLID, borderwidth=1,
            font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()
