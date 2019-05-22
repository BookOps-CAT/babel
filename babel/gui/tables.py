from tkinter import *
from tkinter.ttk import *

from PIL import Image, ImageTk


from data.datastore import (Audn, Branch, DistGridSet, DistGrid,
                            MatType, Lang, Library, User, Vendor,
                            VendorCode)
from gui.data_retriever import get_names
from gui.fonts import RFONT


class DetailsView(Frame):
    """
    Widget displaying elements of each construct
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
        self.unit = app_data['unit']
        self.unit.trace('w', self.unit_observer)


    self.system_observer(self, *args):
        pass

    self.unit_observer(self, *args):
        pass

    self.oberver(self, *args):
        pass


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
        list_height = int((self.winfo_screenheight() - 60) / 20)

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
        self.detLst.bind('<Double-Button-1>', self.populate_detail_list)
        self.detLst.grid(
            row=1, column=3, rowspan=40, sticky='snew')
        scrollbarB['command'] = self.detLst.yview

        # action buttons
        img = Image.open('./icons/Action-edit-add-iconM.png')
        addImg = ImageTk.PhotoImage(img)
        self.addBtn = Button(
            self,
            image=addImg,
            command=None)
        self.addBtn.image = addImg
        self.addBtn.grid(
            row=1, column=5, sticky='sw', padx=20, pady=10)

        img = Image.open('./icons/Action-reload-iconM.png')
        editImg = ImageTk.PhotoImage(img)
        self.editBtn = Button(
            self,
            image=editImg,
            command=None)
        self.editBtn.image = editImg
        self.editBtn.grid(
            row=2, column=5, sticky='sw', padx=20, pady=5)

        img = Image.open('./icons/Action-cancel-iconM.png')
        deleteImg = ImageTk.PhotoImage(img)
        self.deleteBtn = Button(
            self,
            image=deleteImg,
            command=None)
        self.deleteBtn.image = deleteImg
        self.deleteBtn.grid(
            row=3, column=5, sticky='sw', padx=20, pady=5)

        img = Image.open('./icons/Action-ok-iconM.png')
        saveImg = ImageTk.PhotoImage(img)
        self.saveBtn = Button(
            self,
            image=saveImg,
            command=None)
        self.saveBtn.image = saveImg
        self.saveBtn.grid(
            row=4, column=5, sticky='sw', padx=20, pady=5)

    def populate_detail_list(self, *args):
        # detelet current one
        self.detLst.delete(0, END)

        # retrieve data
        table = self.genLst.get(ACTIVE)
        self.gen_list_select.set(table)
        kwargs = {}
        if self.system.get():
            if table == 'Branches':
                model = Branch
                kwargs['system_id'] = self.system.get()
            if table == 'Selectors':
                model = User
            if table == 'Material Types':
                model = MatType
            if table == 'Languages':
                model = Lang
            if table == 'Grids':
                model = DistGrid
            if table == 'Shelf Codes':
                model = ShelfCode
            if table == 'Vendors':
                model = Vendor

            # repopulate
            values = get_names(model, **kwargs)
            for v in values:
                self.detLst.insert(END, v)

    def system_observer(self, *args):
        if self.gen_list_select.get():
            self.populate_detail_list()

    def observer(self, *args):
        if self.activeW.get() == 'TableView':
            pass
