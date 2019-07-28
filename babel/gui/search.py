# Search toplevel widget

import logging
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox


from errors import BabelError
from gui.data_retriever import convert4display
from gui.fonts import RFONT
from gui.utils import BusyManager


mlogger = logging.getLogger('babel_logger')


class SearchView:
    """
    Widget for editing Resource records
    """

    def __init__(self, parent, **app_data):
        self.parent = parent
        self.app_data = app_data

        self.top = Toplevel(master=self.parent)
        self.top.title('Search')
        self.cur_manager = BusyManager(self.top)

        # icons
        self.searchImg = self.app_data['img']['viewS']

        # variables
        self.identifier = StringVar()
        self.identifier_type = StringVar()
        self.title = StringVar()
        self.title_type = StringVar()
        self.cart = StringVar()
        self.cart_type = StringVar()
        self.system = StringVar()
        self.library = StringVar()
        self.profile = StringVar()
        self.audience = StringVar()
        self.language = StringVar()
        self.mattype = StringVar()
        self.vendor = StringVar()
        self.created_start = StringVar()
        self.created_end = StringVar()

        id_values = [
            'bib #',
            'blanketPO',
            'ISBN',
            'order #',
            'other no.',
            'UPC',
            'wlo #'
        ]

        search_types = ['keyword', 'phrase']
        conjunctions = ['and', 'or', 'not']

        # basic search frame
        bfrm = LabelFrame(self.top, text='Basic search')
        bfrm.grid(
            row=0, column=0, sticky='snew', padx=15, pady=15)

        idEnt = Entry(
            bfrm,
            font=RFONT,
            textvariable=self.identifier)
        idEnt.grid(
            row=0, column=0, sticky='new', padx=5, pady=15)

        idtypeCbx = Combobox(
            bfrm,
            font=RFONT,
            state='readonly',
            width=10,
            values=id_values)
        idtypeCbx.grid(
            row=0, column=1, sticky='new', padx=5, pady=15)

        bsearchBtn = Button(
            bfrm,
            image=self.searchImg,
            command=self.basic_search)
        bsearchBtn.grid(
            row=0, column=2, sticky='new', padx=5, pady=10)

        # advanced search frame
        afrm = LabelFrame(self.top, text='Advanced search')
        afrm.grid(
            row=1, column=0, sticky='snew', padx=15, pady=15)

        Label(afrm, text='title:').grid(
            row=0, column=1, sticky='new', padx=5, pady=15)

        titleEnt = Entry(
            afrm,
            font=RFONT,
            textvariable=self.title)
        titleEnt.grid(
            row=0, column=2, columnspan=2, sticky='new', padx=5, pady=15)

        titletypeCbx = Combobox(
            afrm,
            font=RFONT,
            state='readonly',
            width=10,
            values=search_types)
        titletypeCbx.grid(
            row=0, column=4, sticky='new', padx=5, pady=15)

        asearchBtn = Button(
            afrm,
            image=self.searchImg,
            command=self.advanced_search)
        asearchBtn.grid(
            row=0, column=5, sticky='snew', padx=5, pady=10)

        con1Cbx = Combobox(
            afrm,
            font=RFONT,
            state='readonly',
            width=4,
            values=conjunctions)
        con1Cbx.grid(
            row=1, column=0, sticky='new', padx=5, pady=15)

        Label(afrm, text='cart:').grid(
            row=1, column=1, sticky='new', padx=5, pady=15)

        cartEnt = Entry(
            afrm,
            font=RFONT,
            textvariable=self.cart)
        cartEnt.grid(
            row=1, column=2, columnspan=2, sticky='new', padx=5, pady=15)

        carttypeCbx = Combobox(
            afrm,
            font=RFONT,
            state='readonly',
            width=10,
            values=search_types)
        carttypeCbx.grid(
            row=1, column=4, sticky='new', padx=5, pady=15)

    def basic_search(self):
        pass


    def advanced_search(self):
        pass