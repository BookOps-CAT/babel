import logging
from tkinter import *
from tkinter.ttk import *


from logging_settings import LogglyAdapter
from gui.utils import BusyManager
from gui.fonts import RBFONT, RFONT


mlogger = LogglyAdapter(logging.getLogger('babel'), None)


class ReportView(Frame):
    """
    Displays user and combined statistics for all clients
    """

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        Frame.__init__(self, parent)
        self.controller = controller
        self.activeW = app_data['activeW']
