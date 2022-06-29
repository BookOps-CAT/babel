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
        self.top.iconbitmap("./icons/playstation-circle-icon.ico")
        self.cur_manager = BusyManager(self.top)

        # pass resource.did to be able to retrieve it's data
        # and query middleware
        # self.cart_id = app_data["active_id"]
        frm = Frame(self.top)
        frm.grid(row=0, column=0, sticky="snw")

        self.resultsTxt = Text(
            frm,
            width=125,
            state=("disabled"),
            # wrap=WORD,
            background="SystemButtonFace",
            borderwidth=0,
        )
        self.resultsTxt.grid(row=0, column=0, sticky="nsw", padx=20, pady=20)

        scrollbar = Scrollbar(frm, orient=VERTICAL)
        scrollbar.grid(row=0, column=1, sticky="snw")

        self.resultsTxt.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.resultsTxt.yview)

        self.display_data()

    def display_data(self):
        self.resultsTxt["state"] = "normal"
        row = 1
        for bib, items in self.dups_data:
            self.resultsTxt.insert(END, f"b{bib['bibNo']}a\n")
            self.resultsTxt.tag_add("bibNo", f"{row}.0", f"{row}.end")
            self.resultsTxt.insert(END, f"{bib['title']} / {bib['author']}\n")
            self.resultsTxt.tag_add("title", f"{row+1}.0", f"{row+1}.end")
            self.resultsTxt.insert(END, f"{bib['pubPlace']} {bib['pubDate']}\n")
            self.resultsTxt.insert(
                END,
                "\t{0:^5s} | {1:^60s} | {2:^20s} | {3:^7s} | {4:^10s}\n".format(
                    "code", "location", "status", "circ", "lastCheck"
                ),
            )
            self.resultsTxt.insert(END, "\t" + "-" * 114 + "\n")
            row += 6
            if items:
                for i in items:
                    row += 1
                    self.resultsTxt.insert(
                        END,
                        "\t{0:<5s} | {1:<60s} | {2:<20s} | {3:<7s} | {4:<10s}\n".format(
                            i["locCode"],
                            i["locName"],
                            i["status"],
                            i["circ"],
                            i["lastCheck"],
                        ),
                    )
                self.resultsTxt.insert(END, "\n")

        self.resultsTxt.tag_config(
            "bibNo", font=("device", "10", "bold"), foreground="blue2"
        )
        self.resultsTxt.tag_config(
            "title", font=("device", "10", "bold"), foreground="black"
        )
        self.resultsTxt["state"] = "disable"
