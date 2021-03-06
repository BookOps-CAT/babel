# Search toplevel widget

import logging
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox


from data.datastore import (System, Library, User, Lang, Audn,
                            MatType, Vendor, Fund)
from errors import BabelError
from gui.data_retriever import get_names, get_codes
from gui.fonts import RFONT, RBFONT
from gui.utils import BusyManager, ToolTip
from data.transactions_search import get_data_by_identifier, complex_search
from logging_settings import LogglyAdapter


mlogger = LogglyAdapter(logging.getLogger('babel'), None)


class SearchView:
    """
    Widget for editing Resource records
    """

    def __init__(self, parent, **app_data):
        self.parent = parent
        self.app_data = app_data

        mlogger.debug('SearchView active.')

        self.top = Toplevel(master=self.parent)
        self.top.title('Search carts')
        self.cur_manager = BusyManager(self.top)

        # icons
        self.searchImg = self.app_data['img']['viewS']

        # variables
        self.identifier = StringVar()
        self.identifier_type = StringVar()
        self.title = StringVar()
        self.title_type = StringVar()
        self.title_type.set('keyword')
        self.system = StringVar()
        self.library = StringVar()
        self.profile = StringVar()
        self.audn = StringVar()
        self.lang = StringVar()
        self.mattype = StringVar()
        self.vendor = StringVar()
        self.fund = StringVar()
        self.created_start = StringVar()
        self.created_end = StringVar()
        self.con1 = StringVar()
        self.con2 = StringVar()
        self.con3 = StringVar()
        self.con4 = StringVar()
        self.con5 = StringVar()
        self.con6 = StringVar()
        self.con7 = StringVar()
        self.con8 = StringVar()
        self.con9 = StringVar()

        id_values = [
            'bib #',
            'blanketPO',
            'ISBN',
            'order #',
            'other #',
            'UPC',
            'wlo #'
        ]

        search_types = ['keyword', 'phrase']
        conjunctions = ['AND', 'OR', 'NOT', '']
        self.get_comboboxes_values()
        date_format_msg = 'format: YYYY-MM-DD'

        # register validators
        self.vldt = (self.top.register(self.onValidateDate),
                     '%i', '%d', '%P')

        # basic search frame
        bfrm = LabelFrame(self.top, text='Basic search')
        bfrm.grid(
            row=0, column=0, sticky='snew', padx=25, pady=25)

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
            values=id_values,
            textvariable=self.identifier_type)
        idtypeCbx.grid(
            row=0, column=1, sticky='new', padx=5, pady=15)

        bsearchBtn = Button(
            bfrm,
            image=self.searchImg,
            command=self.basic_search)
        bsearchBtn.grid(
            row=0, column=2, sticky='new', padx=5, pady=10)
        self.createToolTip(bsearchBtn, 'run search')

        # advanced search frame
        afrm = LabelFrame(self.top, text='Advanced search')
        afrm.grid(
            row=1, column=0, sticky='snew', padx=25, pady=25)

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
        self.createToolTip(asearchBtn, 'run search')

        con1Cbx = Combobox(
            afrm,
            font=RFONT,
            state='readonly',
            width=4,
            textvariable=self.con1,
            values=conjunctions)
        con1Cbx.grid(
            row=1, column=0, sticky='new', padx=5, pady=2)

        Label(afrm, text='system:').grid(
            row=1, column=1, sticky='new', padx=5, pady=2)

        systemCbx = Combobox(
            afrm,
            font=RFONT,
            state='readonly',
            width=10,
            values=self.system_names)
        systemCbx.grid(
            row=1, column=2, sticky='new', padx=5, pady=2)

        con2Cbx = Combobox(
            afrm,
            font=RFONT,
            width=4,
            state='readonly',
            textvariable=self.con2,
            values=conjunctions)
        con2Cbx.grid(
            row=2, column=0, sticky='new', padx=5, pady=2)

        Label(afrm, text='library:').grid(
            row=2, column=1, sticky='new', padx=5, pady=2)

        libraryCbx = Combobox(
            afrm,
            font=RFONT,
            width=10,
            textvariable=self.library,
            values=self.library_names,
            state='readonly')
        libraryCbx.grid(
            row=2, column=2, sticky='new', padx=5, pady=2)

        con3Cbx = Combobox(
            afrm,
            font=RFONT,
            width=4,
            state='readonly',
            textvariable=self.con3,
            values=conjunctions)
        con3Cbx.grid(
            row=3, column=0, sticky='new', padx=5, pady=2)

        Label(afrm, text='language:').grid(
            row=3, column=1, sticky='new', padx=5, pady=2)

        langCbx = Combobox(
            afrm,
            font=RFONT,
            width=10,
            textvariable=self.lang,
            values=self.lang_names,
            state='readonly')
        langCbx.grid(
            row=3, column=2, sticky='new', padx=5, pady=2)

        con4Cbx = Combobox(
            afrm,
            font=RFONT,
            width=4,
            state='readonly',
            textvariable=self.con4,
            values=conjunctions)
        con4Cbx.grid(
            row=4, column=0, sticky='new', padx=5, pady=2)

        Label(afrm, text='vendor:').grid(
            row=4, column=1, sticky='new', padx=5, pady=2)

        vendorCbx = Combobox(
            afrm,
            font=RFONT,
            width=10,
            state='readonly',
            textvariable=self.vendor,
            values=self.vendor_names)
        vendorCbx.grid(
            row=4, column=2, sticky='new', padx=5, pady=2)

        con5Cbx = Combobox(
            afrm,
            font=RFONT,
            width=4,
            state='readonly',
            textvariable=self.con5,
            values=conjunctions)
        con5Cbx.grid(
            row=5, column=0, sticky='new', padx=5, pady=2)

        Label(afrm, text='audience:').grid(
            row=5, column=1, sticky='new', padx=5, pady=2)

        audnCbx = Combobox(
            afrm,
            font=RFONT,
            width=10,
            state='readonly',
            textvariable=self.audn,
            values=self.audn_names)
        audnCbx.grid(
            row=5, column=2, sticky='new', padx=5, pady=2)

        con6Cbx = Combobox(
            afrm,
            font=RFONT,
            width=4,
            state='readonly',
            textvariable=self.con6,
            values=conjunctions)
        con6Cbx.grid(
            row=6, column=0, sticky='new', padx=5, pady=2)

        Label(afrm, text='mat. type:').grid(
            row=6, column=1, sticky='new', padx=5, pady=2)

        mattypeCbx = Combobox(
            afrm,
            font=RFONT,
            width=10,
            state='readonly',
            textvariable=self.mattype,
            values=self.mattype_names)
        mattypeCbx.grid(
            row=6, column=2, sticky='new', padx=5, pady=2)

        con7Cbx = Combobox(
            afrm,
            font=RFONT,
            width=4,
            state='readonly',
            textvariable=self.con7,
            values=conjunctions)
        con7Cbx.grid(
            row=7, column=0, sticky='new', padx=5, pady=2)

        Label(afrm, text='fund:').grid(
            row=7, column=1, sticky='new', padx=5, pady=2)

        fundCbx = Combobox(
            afrm,
            font=RFONT,
            width=10,
            state='readonly',
            textvariable=self.fund,
            values=self.fund_codes)
        fundCbx.grid(
            row=7, column=2, sticky='new', padx=5, pady=2)

        con8Cbx = Combobox(
            afrm,
            font=RFONT,
            width=4,
            state='readonly',
            textvariable=self.con8,
            values=conjunctions)
        con8Cbx.grid(
            row=8, column=0, sticky='new', padx=5, pady=2)

        Label(afrm, text='profile:').grid(
            row=8, column=1, sticky='new', padx=5, pady=2)

        profileCbx = Combobox(
            afrm,
            font=RFONT,
            width=10,
            state='readonly',
            textvariable=self.profile,
            values=self.profile_names)
        profileCbx.grid(
            row=8, column=2, sticky='new', padx=5, pady=2)

        con9Cbx = Combobox(
            afrm,
            font=RFONT,
            width=4,
            state='readonly',
            textvariable=self.con9,
            values=(conjunctions[0], conjunctions[3]))
        con9Cbx.grid(
            row=9, column=0, sticky='new', padx=5, pady=2)

        Label(afrm, text='date:').grid(
            row=9, column=1, sticky='new', padx=5, pady=2)

        datestartEnt = Entry(
            afrm,
            font=RFONT,
            width=10,
            textvariable=self.created_start,
            validate="key", validatecommand=self.vldt)
        datestartEnt.grid(
            row=9, column=2, sticky='new', padx=5, pady=2)
        self.createToolTip(datestartEnt, date_format_msg)

        dateendEnt = Entry(
            afrm,
            font=RFONT,
            width=14,
            textvariable=self.created_end,
            validate="key", validatecommand=self.vldt)
        dateendEnt.grid(
            row=9, column=3, sticky='new', padx=5, pady=2)
        self.createToolTip(dateendEnt, date_format_msg)

    def basic_search(self):
        if self.identifier.get() and self.identifier_type.get():
            self.cur_manager.busy()
            try:
                data = get_data_by_identifier(
                    self.identifier.get(),
                    self.identifier_type.get())
                self.cur_manager.notbusy()
                self.results_widget(data)
            except BabelError as e:
                self.cur_manager.notbusy()
                messagebox.showerror(
                    'Search error',
                    e, parent=self.top)
        else:
            messagebox.showwarning(
                'Missing input',
                "Please enter identifier and it's type.",
                parent=self.top)

    def advanced_search(self):
        if self.title.get() or \
                (self.created_start.get() and
                    self.created_end.get() and
                    self.con9.get()):
            messagebox.showwarning(
                'Under contruction',
                'Advanced search will be released in the next iteration\n'
                'of Babel app.',
                parent=self.top)

        #     conditions = dict(
        #         title=(self.title.get(), self.title_type.get()),
        #         system=(self.con1.get(), self.system.get()),
        #         library=(self.con2.get(), self.library.get()),
        #         lang=(self.con3.get(), self.lang.get()),
        #         vendor=(self.con4.get(), self.vendor.get()),
        #         audn=(self.con5.get(), self.audn.get()),
        #         mattype=(self.con6.get(), self.mattype.get()),
        #         fund=(self.con7.get(), self.fund.get()),
        #         profile=(self.con8.get(), self.profile.get()),
        #         date=(
        #             self.con9.get(),
        #             self.created_start.get(), self.created_end.get()))
        #     try:
        #         data = complex_search(conditions)
        #     except BabelError as e:
        #         messagebox.showerror(
        #             'Search error',
        #             'Unable to retrieve records.\n'
        #             f'Error: {e}',
        #             parent=self.top)

        # else:
        #     messagebox.showwarning(
        #         'Search warning',
        #         'Your search must be narrowed down.\n'
        #         'Please select additional filters.',
        #         parent=self.top)

    def results_widget(self, data):
        self.restop = Toplevel(master=self.top)
        self.top.title('Search carts restults')

        frm = Frame(self.restop)
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

        self.populate_results(resultsTxt, data)

    def populate_results(self, widget, data):
        widget['state'] = 'normal'

        widget.insert('1.0', f'found {len(data)} hit(s).\n\n')
        widget.tag_add('res_info', '1.0', '1.end')

        ln = 3
        headers = []
        lib_info = []
        for d in data:
            widget.insert(
                f'{ln}.0', f"{d['title']} / {d['author']}\n")
            headers.append(ln)
            ln += 1

            widget.insert(
                f'{ln}.0',
                f"ISBN:{d['isbn']} | UPC:{d['upc']} | other #:{d['other_no']}\n")
            ln += 1

            widget.insert(
                f'{ln}.0',
                f"system:{d['system']} | library: {d['library']}\n")
            lib_info.append(ln)
            ln += 1

            widget.insert(
                f'{ln}.0',
                f"wlo:{d['wlo']} | order #:{d['oid']} | bib #:{d['bid']}\n")
            ln += 1

            widget.insert(
                f'{ln}.0',
                f"owner:{d['owner']} | cart:{d['cart']} | status:{d['status']} | created:{d['created']}\n")
            ln += 1

            widget.insert(
                f'{ln}.0',
                f"vendor:{d['vendor']} | language:{d['lang']}\n")
            ln += 1

            widget.insert(
                f'{ln}.0',
                f"audience:{d['audn_name']} | mat.type:{d['mattype']} | PO:{d['po']}\n")
            ln += 1

            widget.insert(
                f'{ln}.0',
                f"locations: {d['locs']}\n\n")
            ln += 2

        for h in headers:
            widget.tag_add('header', f'{h}.0', f'{h}.end')

        for li in lib_info:
            widget.tag_add('lib_info', f'{li}.7', f'{li}.10')
            widget.tag_add('lib_info', f'{li}.22', f'{li}.end')

        widget.tag_config('res_info', font=RBFONT, foreground='tomato2')
        widget.tag_config('header', font=RFONT, foreground='tomato2')
        widget.tag_config('lib_info', font=RFONT)

        widget['state'] = 'disable'

    def get_comboboxes_values(self):
        mlogger.info('SearchView getting comoboxes values')
        self.system_names = get_names(System)
        self.library_names = get_names(Library)
        self.lang_names = get_names(Lang)
        self.vendor_names = get_names(Vendor)
        self.audn_names = get_names(Audn)
        self.mattype_names = get_names(MatType)
        self.fund_codes = get_codes(Fund)
        self.profile_names = get_names(User)

    def onValidateDate(self, i, d, P):
        valid = True
        if d == '1':
            if i == '0':
                if P != '2':
                    valid = False
            if i in ('1235689'):
                if not P[int(i)].isdigit():
                    valid = False

            if i in ('47'):
                if P[int(i)] != '-':
                    valid = False

            if i == '5':
                if int(P[5]) > 1:
                    valid = False

            if i == '8':
                if int(P[8]) > 3:
                    valid = False

        return valid

    def createToolTip(self, widget, text):
        toolTip = ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)
