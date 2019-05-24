from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox

from PIL import Image, ImageTk


from data.datastore import (Audn, Branch, DistGridSet, DistGrid,
                            MatType, Lang, Library, User, Vendor,
                            VendorCode)
from errors import BabelError
from gui.data_retriever import get_names, get_record, save_record, delete_records
from gui.fonts import RFONT
from gui.utils import disable_widgets, enable_widgets


class TableView(Frame):
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
        self.gen_list_select = StringVar()
        self.det_list_select = StringVar()
        self.det_list_select.trace('w', self.recreate_details_frame)
        self.records = []
        list_height = int((self.winfo_screenheight() - 100) / 25)

        # temp
        self.r = 0

        # layout
        self.columnconfigure(0, minsize=200)  # genLst col
        self.columnconfigure(2, minsize=5)
        self.columnconfigure(3, minsize=300)  # detLst col

        # tables list
        Label(self, text='Tables:').grid(
            row=0, column=0, sticky='nw')
        scrollbarA = Scrollbar(self, orient=VERTICAL)
        scrollbarA.grid(
            row=1, column=1, rowspan=40, sticky='nsw')
        self.genLst = Listbox(
            self,
            font=RFONT,
            height=list_height,
            selectmode=SINGLE,
            yscrollcommand=scrollbarA.set)
        self.genLst.bind('<Double-Button-1>', self.populate_detail_list)
        self.genLst.grid(
            row=1, column=0, rowspan=40, sticky='snew')
        scrollbarA['command'] = self.genLst.yview
        # populate tables list
        tables = [
            'Audineces',
            'Branches',
            'Grids',
            'Languages',
            'Material Types',
            'Selectors',
            'Shelf Codes',
            'Vendors']
        for t in tables:
            self.genLst.insert(END, t)

        # table values list
        self.detLbl = Label(self, textvariable=self.gen_list_select)
        self.detLbl.grid(
            row=0, column=3, sticky='nw')
        scrollbarB = Scrollbar(self, orient=VERTICAL)
        scrollbarB.grid(
            row=1, column=4, rowspan=40, sticky='nsw')
        self.detLst = Listbox(
            self,
            font=RFONT,
            height=list_height,
            yscrollcommand=scrollbarB.set)
        self.detLst.bind('<Double-Button-1>', self.show_details)
        self.detLst.grid(
            row=1, column=3, rowspan=40, sticky='snew')
        scrollbarB['command'] = self.detLst.yview

        # action buttons
        img = Image.open('./icons/Action-edit-add-iconM.png')
        addImg = ImageTk.PhotoImage(img)
        self.addBtn = Button(
            self,
            image=addImg,
            command=self.add_data)
        self.addBtn.image = addImg
        self.addBtn.grid(
            row=1, column=5, sticky='sw', padx=20, pady=10)

        img = Image.open('./icons/Action-reload-iconM.png')
        editImg = ImageTk.PhotoImage(img)
        self.editBtn = Button(
            self,
            image=editImg,
            command=self.edit_data)
        self.editBtn.image = editImg
        self.editBtn.grid(
            row=2, column=5, sticky='sw', padx=20, pady=5)

        img = Image.open('./icons/Action-cancel-iconM.png')
        deleteImg = ImageTk.PhotoImage(img)
        self.deleteBtn = Button(
            self,
            image=deleteImg,
            command=self.delete_data)
        self.deleteBtn.image = deleteImg
        self.deleteBtn.grid(
            row=3, column=5, sticky='sw', padx=20, pady=5)

        img = Image.open('./icons/Action-ok-iconM.png')
        saveImg = ImageTk.PhotoImage(img)
        self.saveBtn = Button(
            self,
            image=saveImg,
            command=self.insert_or_update_data)
        self.saveBtn.image = saveImg
        self.saveBtn.grid(
            row=4, column=5, sticky='sw', padx=20, pady=5)

        self.initiate_details_frame()

    def add_data(self):
        # redo details frame
        self.recreate_details_frame()

        # activate only when a table is selected
        table = self.gen_list_select.get()
        if table:
            if table in ('Audiences', 'Branches', 'Languages'):
                self.simpleDetailFrame()

            enable_widgets(self.detFrm.winfo_children())

    def edit_data(self):
        self.recreate_details_frame()
        table = self.gen_list_select.get()
        if table:
            if table in ('Audiences', 'Branches', 'Languages'):
                self.populate_detail_frame(table)

            enable_widgets(self.detFrm.winfo_children())

    def delete_data(self):
        # ask before deletion
        if self.records:
            msg = 'Are you sure you want to delete\n{}?'.format(
                '\n'.join([str(x) for x in self.records]))
            if messagebox.askokcancel('Deletion', msg):
                delete_records(self.records)
                self.populate_detail_list()
                self.detFrm.destroy()
                self.initiate_details_frame()
                self.records = []

    def insert_or_update_data(self):
        # check what table it is
        table = self.gen_list_select.get()
        kwargs = {}
        error_msg = False
        if self.records:
            for record in self.records:
                if table in ('Audiences', 'Branches', 'Languages'):
                    name = self.nameEnt.get().strip()
                    code = self.codeEnt.get().strip()
                    kwargs = {
                        'name': name,
                        'code': code}

                for k, v in kwargs.items():
                    if v == '':
                        kwargs[k] = None
                model, kwargs = self.identify_model(table, **kwargs)
                try:
                    save_record(
                        model, did=record.did, **kwargs)
                except BabelError as e:
                    error_msg = True
                    messagebox.showerror('Database error', e)

        else:
            if table in ('Audiences', 'Branches', 'Languages'):
                name = self.nameEnt.get()
                code = self.codeEnt.get()
                # validate
                kwargs = {
                    'name': name,
                    'code': code}

            for k, v in kwargs.items():
                if v == '':
                    kwargs[k] = None
            model, kwargs = self.identify_model(table, **kwargs)
            try:
                save_record(
                    model, **kwargs)
            except BabelError as e:
                error_msg = True
                messagebox.showerror('Database error', e)
        self.populate_detail_list(redo_detail_frame=False)
        if not error_msg:
            disable_widgets(self.detFrm.winfo_children())

    def identify_model(self, table, **kwargs):
        if not kwargs:
            kwargs = {}
        if table == 'Selectors':
            model = User
        elif table == 'Material Types':
            model = MatType
        elif table == 'Languages':
            model = Lang
        elif self.system.get():
            kwargs['system_id'] = self.system.get()
            if table == 'Audineces':
                model = Audn
            elif table == 'Branches':
                model = Branch
            elif table == 'Grids':
                model = DistGrid
            elif table == 'Shelf Codes':
                model = ShelfCode
            elif table == 'Vendors':
                model = Vendor
        else:
            model = None
        return (model, kwargs)

    def show_details(self, *args):
        table = self.gen_list_select.get()
        self.det_list_select.set(self.detLst.get(ACTIVE))

        if table in ('Audiences', 'Branches', 'Languages'):
            self.populate_detail_frame(table)

    def populate_detail_frame(self, table):
        model = self.identify_model(table)[0]
        if table in ('Audiences', 'Branches', 'Languages'):
            record = get_record(model, name=self.det_list_select.get())
            self.records = [record]
            self.simpleDetailFrame(record.name, record.code)

    def simpleDetailFrame(self, name='', code=''):
        Label(self.detFrm, text='name').grid(
            row=0, column=0, sticky='snw', padx=5, pady=5)
        Label(self.detFrm, text='code').grid(
            row=1, column=0, sticky='snw', padx=5, pady=5)
        self.nameEnt = Entry(
            self.detFrm,
            font=RFONT)
        self.nameEnt.grid(
            row=0, column=1, columnspan=3, padx=5, pady=5)
        self.codeEnt = Entry(
            self.detFrm,
            font=RFONT,)
        self.codeEnt.grid(
            row=1, column=1, columnspan=3, padx=5, pady=5)
        self.nameEnt.insert(0, name)
        self.codeEnt.insert(0, code)
        disable_widgets([self.nameEnt, self.codeEnt])

    def initiate_details_frame(self):
        # Details frame
        self.detFrm = LabelFrame(self, text='Values')
        self.detFrm.grid(row=1, column=6, rowspan=40, sticky='snew', padx=5)

    def recreate_details_frame(self, *args):
        self.detFrm.destroy()
        self.records = []
        self.initiate_details_frame()

    def populate_detail_list(self, redo_detail_frame=True, *args):
        # destroy any detail frame that may display
        # previous data
        if redo_detail_frame:
            self.recreate_details_frame()

        # detelet current detail list
        self.detLst.delete(0, END)

        # retrieve data
        table = self.genLst.get(ACTIVE)
        self.gen_list_select.set(table)

        # repopulate
        model, kwargs = self.identify_model(table)
        if model is not None:
            values = get_names(model, **kwargs)
            for v in values:
                self.detLst.insert(END, v)

    def system_observer(self, *args):
        if self.gen_list_select.get():
            self.populate_detail_list()

    def observer(self, *args):
        if self.activeW.get() == 'TableView':
            pass
