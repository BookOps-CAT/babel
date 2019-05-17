from tkinter import *
from tkinter.ttk import *


class ReportView(Frame):
    """
    Displays user and combined statistics for all clients
    """

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        Frame.__init__(self, parent)
        self.controller = controller
        self.activeW = app_data['activeW']
