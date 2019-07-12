import logging
import shelve
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox

from PIL import Image, ImageTk


from errors import BabelError
from data.datastore import (Audn, Branch, Fund, Library, MatType)
from gui.data_retriever import (get_codes, get_names, get_record,
                                get_fund_data, update_fund,
                                insert_fund, delete_data)
from gui.fonts import RFONT
from gui.utils import disable_widgets, enable_widgets
from paths import USER_DATA


mlogger = logging.getLogger('babel_logger')


class FundView(Frame):
    """
    Shared among settings widgets frame
    """

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        Frame.__init__(self, parent)
        self.controller = controller
        self.app_data = app_data
        self.activeW = app_data['activeW']
        self.activeW.trace('w', self.observer)
        self.profile = app_data['profile']
        self.system = app_data['system']
        self.system.trace('w', self.system_observer)
        list_height = int((self.winfo_screenheight() - 100) / 25)

        self.record = None
        self.all_branches = IntVar()
        self.all_branches.trace('w', self.branch_selection_observer)
        self.all_branchesLbl = StringVar()
        self.all_branchesLbl.set('select all')
        self.fund_code = StringVar()
        self.fund_desc = StringVar()

        # pull icons from main img dictionary instead to preserve memory
        # setup small add/remove icons
        img = Image.open('./icons/Action-edit-add-iconS.png')
        addSImg = ImageTk.PhotoImage(img)
        img = Image.open('./icons/Action-remove-iconS.png')
        removeSImg = ImageTk.PhotoImage(img)

        # tables list
        Label(self, text='Funds:').grid(
            row=0, column=0, sticky='nw')
        scrollbarA = Scrollbar(self, orient=VERTICAL)
        scrollbarA.grid(
            row=1, column=1, rowspan=40, sticky='nsw')
        self.fundLst = Listbox(
            self,
            font=RFONT,
            height=list_height,
            selectmode=SINGLE,
            yscrollcommand=scrollbarA.set)
        self.fundLst.bind('<Double-Button-1>', self.show_fund)
        self.fundLst.grid(
            row=1, column=0, rowspan=40, sticky='snew')
        scrollbarA['command'] = self.fundLst.yview

        # action buttons
        img = Image.open('./icons/Action-edit-add-iconM.png')
        addImg = ImageTk.PhotoImage(img)
        self.addBtn = Button(
            self,
            image=addImg,
            command=self.add_data)
        self.addBtn.image = addImg
        self.addBtn.grid(
            row=1, column=5, sticky='sw', padx=10, pady=10)

        img = Image.open('./icons/Action-reload-iconM.png')
        editImg = ImageTk.PhotoImage(img)
        self.editBtn = Button(
            self,
            image=editImg,
            command=self.edit_data)
        self.editBtn.image = editImg
        self.editBtn.grid(
            row=2, column=5, sticky='sw', padx=10, pady=5)

        img = Image.open('./icons/Action-cancel-iconM.png')
        deleteImg = ImageTk.PhotoImage(img)
        self.deleteBtn = Button(
            self,
            image=deleteImg,
            command=self.delete_data)
        self.deleteBtn.image = deleteImg
        self.deleteBtn.grid(
            row=3, column=5, sticky='sw', padx=10, pady=5)

        img = Image.open('./icons/Action-ok-iconM.png')
        saveImg = ImageTk.PhotoImage(img)
        self.saveBtn = Button(
            self,
            image=saveImg,
            command=self.insert_or_update_data)
        self.saveBtn.image = saveImg
        self.saveBtn.grid(
            row=4, column=5, sticky='sw', padx=10, pady=5)

        img = Image.open('./icons/Action-button-info-iconM.png')
        helpImg = ImageTk.PhotoImage(img)
        self.helpBtn = Button(
            self,
            image=helpImg,
            command=self.help)
        self.helpBtn.image = helpImg
        self.helpBtn.grid(
            row=5, column=5, sticky='sw', padx=10, pady=5)

        # details/edit frame
        self.detFrm = LabelFrame(self, text='Fund code and constraints')
        self.detFrm.grid(
            row=0, column=6, rowspan=40, columnspan=5, sticky='snew')

        # fund data
        self.editFrm = Frame(self.detFrm)
        self.editFrm.grid(
            row=1, column=0, rowspan=5, columnspan=2, sticky='snew',
            padx=2)
        Label(self.editFrm, text='Fund code').grid(
            row=0, column=0, sticky='snw', pady=5)
        self.fundcodeEnt = Entry(
            self.editFrm,
            font=RFONT,
            textvariable=self.fund_code)
        self.fundcodeEnt.grid(
            row=1, column=0, columnspan=3, sticky='snew', pady=5)
        Label(self.editFrm, text='Description').grid(
            row=2, column=0, sticky='snw', pady=5)
        self.funddescEnt = Entry(
            self.editFrm,
            font=RFONT,
            textvariable=self.fund_desc)
        self.funddescEnt.grid(
            row=3, column=0, rowspan=2, columnspan=3, sticky='snew', pady=5)

        Label(self.detFrm, text='out').grid(
            row=0, column=4, columnspan=2, padx=2, sticky='snw')
        Label(self.detFrm, text='in').grid(
            row=0, column=7, columnspan=2, padx=2, sticky='snw')
        Label(self.detFrm, text='out').grid(
            row=0, column=11, columnspan=2, padx=2, sticky='snw')
        Label(self.detFrm, text='in').grid(
            row=0, column=14, columnspan=2, padx=2, sticky='snw')

        # branches
        self.branchFrm = LabelFrame(self.detFrm, text='Branches')
        self.branchFrm.grid(
            row=1, column=4, rowspan=10, columnspan=5,
            sticky='snew', padx=5)

        Checkbutton(
            self.branchFrm, textvariable=self.all_branchesLbl,
            variable=self.all_branches).grid(row=0, column=0, sticky='snw')

        scrollbarB = Scrollbar(self.branchFrm, orient=VERTICAL)
        scrollbarB.grid(
            row=1, column=1, rowspan=20, sticky='nsw', pady=2)
        self.branchOutLst = Listbox(
            self.branchFrm,
            font=RFONT,
            height=list_height,
            width=14,
            selectmode=EXTENDED,
            yscrollcommand=scrollbarB.set)
        self.branchOutLst.grid(
            row=1, column=0, rowspan=20, sticky='snew', padx=2, pady=2)
        scrollbarB['command'] = self.branchOutLst.yview

        self.branchInBtn = Button(
            self.branchFrm,
            image=addSImg,
            command=lambda: self.add_condition(
                'branchLst',
                self.branchOutLst, self.branchInLst,
                self.branchOutLst.curselection()))
        self.branchInBtn.image = addSImg
        self.branchInBtn.grid(
            row=1, column=2, sticky='sw', padx=2, pady=2)

        self.branchOutBtn = Button(
            self.branchFrm,
            image=removeSImg,
            command=lambda: self.remove_condition(
                'branchLst',
                self.branchOutLst, self.branchInLst,
                self.branchInLst.curselection()))
        self.branchOutBtn.image = removeSImg
        self.branchOutBtn.grid(
            row=2, column=2, sticky='sw', padx=2, pady=2)

        scrollbarC = Scrollbar(self.branchFrm, orient=VERTICAL)
        scrollbarC.grid(
            row=1, column=4, rowspan=20, sticky='nsw', pady=2)
        self.branchInLst = Listbox(
            self.branchFrm,
            font=RFONT,
            width=14,
            height=list_height,
            selectmode=EXTENDED,
            yscrollcommand=scrollbarC.set)
        self.branchInLst.grid(
            row=1, column=3, rowspan=20, sticky='snew', padx=2, pady=2)
        scrollbarC['command'] = self.branchInLst.yview

        # library
        self.libraryFrm = LabelFrame(self.detFrm, text='Library')
        self.libraryFrm.grid(
            row=1, column=11, rowspan=2, columnspan=5,
            sticky='snew', padx=5)

        self.libOutLst = Listbox(
            self.libraryFrm,
            font=RFONT,
            width=15,
            height=3,
            selectmode=EXTENDED)
        self.libOutLst.grid(
            row=0, column=0, rowspan=3, sticky='snew', padx=2, pady=2)

        self.libInBtn = Button(
            self.libraryFrm,
            image=addSImg,
            command=lambda: self.add_condition(
                'libLst',
                self.libOutLst, self.libInLst,
                self.libOutLst.curselection()))
        self.libInBtn.image = addSImg
        self.libInBtn.grid(
            row=0, column=1, sticky='sw', padx=5, pady=2)

        self.libOutBtn = Button(
            self.libraryFrm,
            image=removeSImg,
            command=lambda: self.remove_condition(
                'LibLst',
                self.libOutLst, self.libInLst,
                self.libInLst.curselection()))
        self.libOutBtn.image = removeSImg
        self.libOutBtn.grid(
            row=1, column=1, sticky='sw', padx=5, pady=2)

        self.libInLst = Listbox(
            self.libraryFrm,
            font=RFONT,
            height=3,
            width=15,
            selectmode=EXTENDED)
        self.libInLst.grid(
            row=0, column=2, rowspan=2, sticky='snew', padx=2, pady=2)

        # audience
        self.audienceFrm = LabelFrame(self.detFrm, text='Audience')
        self.audienceFrm.grid(
            row=3, column=11, rowspan=2, columnspan=5,
            sticky='snew', padx=5, pady=5)

        self.audnOutLst = Listbox(
            self.audienceFrm,
            font=RFONT,
            width=15,
            height=4,
            selectmode=EXTENDED)
        self.audnOutLst.grid(
            row=0, column=0, rowspan=2, sticky='snew', padx=2, pady=2)

        self.audnInBtn = Button(
            self.audienceFrm,
            image=addSImg,
            command=lambda: self.add_condition(
                'audnLst',
                self.audnOutLst, self.audnInLst,
                self.audnOutLst.curselection()))
        self.audnInBtn.image = addSImg
        self.audnInBtn.grid(
            row=0, column=1, sticky='sw', padx=5, pady=2)

        self.audnOutBtn = Button(
            self.audienceFrm,
            image=removeSImg,
            command=lambda: self.remove_condition(
                'audnLst',
                self.audnOutLst, self.audnInLst,
                self.audnInLst.curselection()))
        self.audnOutBtn.image = removeSImg
        self.audnOutBtn.grid(
            row=1, column=1, sticky='sw', padx=5, pady=2)

        self.audnInLst = Listbox(
            self.audienceFrm,
            font=RFONT,
            width=15,
            height=4,
            selectmode=EXTENDED)
        self.audnInLst.grid(
            row=0, column=2, rowspan=2, sticky='snew', padx=2, pady=2)

        # material type
        self.mattypeFrm = LabelFrame(self.detFrm, text='Material type')
        self.mattypeFrm.grid(
            row=5, column=11, rowspan=7, columnspan=5,
            sticky='snew', padx=5, pady=5)

        self.mattypeOutLst = Listbox(
            self.mattypeFrm,
            font=RFONT,
            width=15,
            height=7,
            selectmode=EXTENDED)
        self.mattypeOutLst.grid(
            row=0, column=0, rowspan=7, sticky='snew', padx=2, pady=2)

        self.mattypeInBtn = Button(
            self.mattypeFrm,
            image=addSImg,
            command=lambda: self.add_condition(
                'mattypeLst',
                self.mattypeOutLst, self.mattypeInLst,
                self.mattypeOutLst.curselection()))
        self.mattypeInBtn.image = addSImg
        self.mattypeInBtn.grid(
            row=0, column=1, sticky='sw', padx=5, pady=2)

        self.mattypeOutBtn = Button(
            self.mattypeFrm,
            image=removeSImg,
            command=lambda: self.remove_condition(
                'mattypesLst',
                self.mattypeOutLst, self.mattypeInLst,
                self.mattypeInLst.curselection()))
        self.mattypeOutBtn.image = removeSImg
        self.mattypeOutBtn.grid(
            row=1, column=1, sticky='sw', padx=5, pady=2)

        self.mattypeInLst = Listbox(
            self.mattypeFrm,
            font=RFONT,
            width=15,
            height=7,
            selectmode=EXTENDED)
        self.mattypeInLst.grid(
            row=0, column=2, rowspan=7, sticky='snew', padx=2, pady=2)

    def show_fund(self, *args):
        mlogger.debug('Displaying fund details.')
        enable_widgets(self.detFrm.winfo_children())
        self.record = get_record(Fund, code=self.fundLst.get(ACTIVE))
        self.display_branches()
        self.display_library()
        self.display_audiences()
        self.display_mattypes()
        fund_data = get_fund_data(self.record)
        mlogger.debug('Fund data: {}'.format(fund_data))

        # display code & description
        self.fund_code.set(fund_data['code'])
        self.fund_desc.set(fund_data['describ'])

        # convert values to listbox indices and add conditions
        # branchLst
        branch_idx = self.get_listbox_indices(
            self.branchOutLst, fund_data['branches'])
        mlogger.debug('branchOutLst index matches: {}'.format(branch_idx))
        self.add_condition(
            'branchLst', self.branchOutLst, self.branchInLst,
            branch_idx)

        # audnLst
        audn_idx = self.get_listbox_indices(
            self.audnOutLst, fund_data['audns'])
        mlogger.debug('audnOutLst index matches: {}'.format(audn_idx))
        self.add_condition(
            'audnLst', self.audnOutLst, self.audnInLst, audn_idx)
        # libLst
        library_idx = self.get_listbox_indices(
            self.libOutLst, fund_data['libraries'])
        mlogger.debug('libOutLst index matches: {}'.format(
            library_idx))
        self.add_condition(
            'libLst', self.libOutLst, self.libInLst, library_idx)

        # mattypeOutLst
        mattype_idx = self.get_listbox_indices(
            self.mattypeOutLst, fund_data['matTypes'])
        mlogger.debug('mattypeOutLst index matches: {}'.format(
            mattype_idx))
        self.add_condition(
            'mattypeLst', self.mattypeOutLst, self.mattypeInLst,
            mattype_idx)

        # lock the interface
        disable_widgets(self.detFrm.winfo_children())

    def add_data(self):
        if self.system.get():
            self.record = None
            self.fund_code.set('')
            self.fund_desc.set('')
            enable_widgets(self.detFrm.winfo_children())
            self.display_branches()
            self.display_library()
            self.display_audiences()
            self.display_mattypes()
        else:
            msg = 'Please select system first.'
            messagebox.showwarning('Input Error', msg)

    def edit_data(self):
        if self.record:
            self.show_fund()
            enable_widgets(self.detFrm.winfo_children())

    def delete_data(self):
        if self.record:
            delete_data(self.record)

    def insert_or_update_data(self):
        missing = []
        if not self.system.get():
            missing.append('system')
        if not self.fund_code.get():
            missing.append('fund code')
        if not self.branchInLst.get(0, END):
            missing.append('valid branches')
        if self.system.get() == 2 and not self.libInLst.get(0, END):
            missing.append('valid library')
        if not self.audnInLst.get(0, END):
            missing.append('valid audiences')
        if not self.mattypeInLst.get(0, END):
            missing.append('valid material types')

        if not missing:
            try:
                kwargs = dict(
                    system_id=self.system.get(),
                    code=self.fund_code.get().strip(),
                    describ=self.fund_desc.get().strip(),
                    branches=self.branchInLst.get(0, END),
                    libraries=self.libInLst.get(0, END),
                    audns=self.audnInLst.get(0, END),
                    matTypes=self.mattypeInLst.get(0, END))

                if not self.record:
                    insert_fund(**kwargs)
                else:
                    update_fund(**kwargs)
                self.display_funds()
                disable_widgets(self.detFrm.winfo_children())
            except BabelError as e:
                messagebox.showerror(e)
        else:
            msg = 'Missing requried elements:\n-{}'.format(
                '\n-'.join(missing))
            messagebox.showwarning(
                'Input Error', msg)

    def help(self):
        pass

    def get_listbox_indices(self, widgetLst, data):
        """
        Given list of values, retrieves their index in listbox (widgetLst)
        args:
            widgetLst: tkinter listbox obj, listbox to be queried
            data: list of strings, values to be queried
        returns:
            indices: list of widgetLst indices for given values
        """

        mlogger.debug('Retrieving indices for values {} in a listbox.'.format(
            data))
        values = widgetLst.get(0, END)
        return [values.index(d) for d in data]

    def add_condition(self, category, widgetOut, widgetIn, selected):
        mlogger.debug('Adding condition(s) to {} initiated.'.format(
            category))
        values = [widgetOut.get(x) for x in selected]
        mlogger.debug('Selected condition values: {}'.format(values))

        # remove them from out widget
        for x in reversed(selected):
            mlogger.debug('Deleting selected {}'.format(x))
            widgetOut.delete(x)

        # sort and add them to in widget
        in_values = list(widgetIn.get(0, END))
        mlogger.debug('Existing values: {}'.format(in_values))
        widgetIn.delete(0, END)
        in_values.extend(values)
        mlogger.debug('Existing values after appending: {}'.format(
            in_values))

        for value in sorted(in_values):
            widgetIn.insert(END, value)

    def remove_condition(self, category, widgetOut, widgetIn, selected):
        mlogger.debug('Removing condition(s) from {} initiated'.format(
            category))

        values = [widgetIn.get(x) for x in selected]
        mlogger.debug('Selected condiction values: {}'.format(values))

        # remove from in widget
        for x in reversed(selected):
            widgetIn.delete(x)

        # sort and add them to out widget
        out_values = list(widgetOut.get(0, END))
        mlogger.debug('Existing values: {}'.format(out_values))
        widgetOut.delete(0, END)
        out_values.extend(values)
        mlogger.debug('Existing values after appending: {}'.format(
            out_values))

        for value in sorted(out_values):
            widgetOut.insert(END, value)

    def display_funds(self):
        self.fundLst.delete(0, END)
        funds = get_codes(Fund, system_id=self.system.get())
        for fund in sorted(funds):
            self.fundLst.insert(END, fund)

    def display_branches(self):
        mlogger.debug('Displaying branches.')
        self.branchOutLst.delete(0, END)
        self.branchInLst.delete(0, END)
        branches = get_codes(Branch, system_id=self.system.get())
        for branch in branches:
            self.branchOutLst.insert(END, branch)

    def display_library(self):
        mlogger.debug('Displaying library.')
        self.libOutLst.delete(0, END)
        self.libInLst.delete(0, END)
        if self.system.get() == 1:
            disable_widgets(self.libraryFrm.winfo_children())
        if self.system.get() == 2:
            enable_widgets(self.libraryFrm.winfo_children())
            libraries = get_names(Library)
            for library in libraries:
                self.libOutLst.insert(END, library)

    def display_audiences(self):
        mlogger.debug('Displaying audiences.')
        self.audnOutLst.delete(0, END)
        self.audnInLst.delete(0, END)
        audns = get_names(Audn)
        for audn in sorted(audns):
            self.audnOutLst.insert(END, audn)

    def display_mattypes(self):
        mlogger.debug('Displaying mattypes.')
        self.mattypeOutLst.delete(0, END)
        self.mattypeInLst.delete(0, END)
        mattypes = get_names(MatType)
        for mattype in sorted(mattypes):
            self.mattypeOutLst.insert(END, mattype)

    def branch_selection_observer(self, *args):
        if self.system.get():
            if self.all_branches.get() == 1:
                # change label
                self.all_branchesLbl.set('deselect all')
                # remove any existing selection
                self.branchInLst.delete(0, END)
                # re-retrive branches in case some were
                # already selected
                self.display_branches()
                branches = self.branchOutLst.get(0, END)
                self.branchOutLst.delete(0, END)
                for branch in branches:
                    self.branchInLst.insert(END, branch)

            elif self.all_branches.get() == 0:
                self.all_branchesLbl.set('select all')
                self.branchInLst.delete(0, END)
                self.branchOutLst.delete(0, END)
                self.display_branches()

    def system_observer(self, *args):
        if self.activeW.get() == 'FundView':
            self.record = None
            enable_widgets(self.detFrm.winfo_children())
            self.display_funds()
            self.all_branches.set(0)
            self.display_branches()
            self.display_audiences()
            self.display_mattypes()

            # enable/disable widgets for library
            self.display_library()
            disable_widgets(self.detFrm.winfo_children())

    def observer(self, *args):
        if self.activeW.get() == 'FundView':
            self.all_branches.set(0)

            # pull data from data store only
            self.display_funds()
            self.display_audiences()
            self.display_mattypes()
            if self.system.get():
                self.display_branches()
                self.display_library()
            disable_widgets(self.detFrm.winfo_children())
