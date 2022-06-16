import logging
from tkinter import *
from tkinter.ttk import *


from gui.fonts import RFONT, RBFONT, LFONT
from gui.utils import BusyManager
from logging_settings improt LogglyAdapter
from reports.cart import format_nypl_sierra_data_for_display, format_bpl_sierra_data_for_display
from sierra_adapters.middleware import catalog_lookup

mlogger = LogglyAdapter(logging.getLogger("babel"), None)


class CatalogDupWidget:
    """Displays Sierra dup information"""

    def __init__(self, parent, **app_data):
        self.parent = parent
        self.app_data = app_data

        mlogger.debug("CartDupWidet activated.")

        self.top = Toplevel(master=self.parent)
        self.top.title("Sierra duplicates")
        self.cur_manager = BusyManager(self.top)

        # pass resource.did to be able to retrieve it's data
        # and query middleware
        # self.cart_id = app_data["active_id"]
        frm = Frame(self.top)
        frm.grid(row=0, column=0, sticky="snw")

        scrollbar = Scrollbar(frm, orient=VERTICAL)
        scrollbar.grid(row=0, column=0, sticky="snw")
        # scrollbar.["command"] = self.frm.y

        # self.resultsTxt = Text()

        # display nice msg if no Sierra/middleware data availalbe

    def query_middleware(self):
        # retrieve resource data from db based on resource.did
        # perform middleware query based on dup_bibs data
        # format that data for display
        # display