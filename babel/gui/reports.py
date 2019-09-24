import logging
from tkinter import *
from tkinter.ttk import *


from logging_settings import LogglyAdapter
from gui.utils import BusyManager
from gui.fonts import RBFONT, RFONT
from reports.cart import tabulate_cart_data


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

        frm = Frame(self.top)
        frm.grid(
            row=0, column=0, sticky='snew', padx=20, pady=20)

        scrollbar = Scrollbar(frm, orient=VERTICAL)
        scrollbar.grid(row=0, column=0, rowspan=5, sticky='snw')

        self.resultsTxt = Text(
            frm,
            wrap='word',
            height=30,
            width=120,
            background='SystemButtonFace',
            borderwidth=0,
            yscrollcommand=scrollbar.set)
        self.resultsTxt.grid(
            row=0, column=1, rowspan=5, sticky="snew", padx=10)
        scrollbar['command'] = self.resultsTxt.yview

        self.tabulate()

    def tabulate(self):
        self.resultsTxt['state'] = 'normal'
        self.resultsTxt.insert(
            '1.0', 'Cart summary:\n\n')
        self.resultsTxt.tag_add('header', '1.0', '1.end')
        branch_headers = []
        branch_data = []

        data = tabulate_cart_data(self.cart_id.get())
        ln = 3
        for b, v in data.items():
            self.resultsTxt.insert(
                f'{ln}.0', f'{b}: titles={v["titles"]}, '
                f'copies={v["copies"]}, dollars={v["dollars"]}\n')
            ln += 1
            for l in range(3, ln):
                self.resultsTxt.tag_add('branch', f'{l}.0', f'{l}.3')
                self.resultsTxt.tag_add('data', f'{l}.4', f'{l}.end')

        self.resultsTxt.tag_config('header', font=RBFONT)
        self.resultsTxt.tag_config('branch', font=RFONT, foreground='tomato2')
        self.resultsTxt.tag_config('data', font=RFONT)


class ReportView(Frame):
    """
    Displays user and combined statistics for all clients
    """

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        Frame.__init__(self, parent)
        self.controller = controller
        self.activeW = app_data['activeW']
