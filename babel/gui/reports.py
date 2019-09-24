import logging
from tkinter import *
from tkinter.ttk import *

from logging_settings import LogglyAdapter
from gui.utils import BusyManager


mlogger = LogglyAdapter(logging.getLogger('babel'), None)


class CartSummary:
    """Displays a report on specific cart; invoked from CartView"""

    def __init__(self, parent, **app_data):

        self.parent = parent
        self.app_data = app_data

        mlogger.debug('CartSummary active.')

        self.top = Toplevel(master=self.parent)
        self.top.title('Cart summary')
        self.cur_manager = BusyManager(self.top)

        self.cart_id = app_data['active_id']
        self.system = app_data['system']
        self.profile = app_data['profile']

        frm = Frame(self.top)
        frm.grid(
            row=0, column=0, sticky='snew', padx=20, pady=20)

        scrollbar = Scrollbar(frm, orient=VERTICAL)
        scrollbar.grid(row=0, column=0, rowspan=5, sticky='snw')

        resultsTxt = Text(
            frm,
            wrap='word',
            height=30,
            width=120,
            background='SystemButtonFace',
            borderwidth=0,
            yscrollcommand=scrollbar.set)
        resultsTxt.grid(
            row=0, column=1, rowspan=5, sticky="snew", padx=10)
        scrollbar['command'] = resultsTxt.yview




class ReportView(Frame):
    """
    Displays user and combined statistics for all clients
    """

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        Frame.__init__(self, parent)
        self.controller = controller
        self.activeW = app_data['activeW']
