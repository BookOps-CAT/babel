import logging
from tkinter import *
from tkinter.ttk import *


from gui.fonts import RFONT, RBFONT, LFONT
from gui.utils import BusyManager
from logging_settings import LogglyAdapter
from reports.cart import (
    format_nypl_sierra_data_for_display,
    format_bpl_sierra_data_for_display,
)

mlogger = LogglyAdapter(logging.getLogger("babel"), None)


class CatalogDupWidget:
    """Displays Sierra dup information"""

    def __init__(self, parent, dups_data):
        self.parent = parent
        self.dups_data = dups_data

        mlogger.debug("CartDupWidet activated.")

        self.top = Toplevel(master=self.parent)
        self.top.title("Sierra duplicates")
        self.cur_manager = BusyManager(self.top)

        # pass resource.did to be able to retrieve it's data
        # and query middleware
        # self.cart_id = app_data["active_id"]
        frm = Frame(self.top)
        frm.grid(row=0, column=0, sticky="snw")

        self.resultsTxt = Text(
            frm,
            width=65,
            state=("disabled"),
            wrap=WORD,
            background="SystemButtonFace",
            borderwidth=0,
        )
        self.resultsTxt.grid(row=0, column=0, sticky="nsw")

        scrollbar = Scrollbar(frm, orient=VERTICAL)
        scrollbar.grid(row=0, column=1, sticky="snw")

        self.resultsTxt.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.resultsTxt.yview)

        self.display_data()

    def display_data(self):
        self.resultsTxt["state"] = "normal"
        for bib_data, items_data in self.dups_data:
            self.resultsTxt.insert(END, f"{bib_data['bibNo']}\n")
            self.resultsTxt.insert(END, f"{bib_data['title']} / {bib_data['author']}\n")
            self.resultsTxt.insert(
                END, f"{bib_data['pubPlace']} - {bib_data['pubDate']}"
            )

        self.resultsTxt["state"] = "disable"
