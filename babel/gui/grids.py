import logging
import shelve
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox

from PIL import Image, ImageTk


from errors import BabelError
from data.datastore import (Audn, Branch, DistSet, DistGrid, Lang, Library, MatType,
                            Vendor, ShelfCode)
from gui.data_retriever import (get_codes, get_names, get_record,
                                delete_data, create_name_index,
                                create_code_index, save_data)
from gui.fonts import RFONT
from gui.utils import (disable_widgets, enable_widgets, get_id_from_index,
                       ToolTip)
from paths import USER_DATA


mlogger = logging.getLogger('babel_logger')


class GridView(Frame):
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
        self.profile_idx = app_data['profile_idx']
        self.system = app_data['system']
        self.system.trace('w', self.system_observer)
        list_height = int((self.winfo_screenheight() - 100) / 25)

        # local variables
        self.distr_name = StringVar()
        self.grid_name = StringVar()
        self.library = StringVar()
        self.lang = StringVar()
        self.vendor = StringVar()
        self.audn = StringVar()
        self.mattype = StringVar()
        self.locations = []
        self.counter = StringVar()

        # records if updates
        self.distr_record = None
        self.grid_record = None

        # indexes to refernce names/codes to datastore id
        self.branch_idx = {}
        self.shelf_idx = {}
        self.lib_idx = {}
        self.lang_idx = {}
        self.vendor_idx = {}
        self.audn_idx = {}
        self.matttype_idx = {}

        # icons
        img = Image.open('./icons/Action-remove-iconS.png')
        self.removeImg = ImageTk.PhotoImage(img)
        img = Image.open('./icons/Action-edit-add-iconS.png')
        self.addImg = ImageTk.PhotoImage(img)
        img = Image.open('./icons/Action-edit-add-iconM.png')
        addImg = ImageTk.PhotoImage(img)
        img = Image.open('./icons/Action-reload-iconM.png')
        editImg = ImageTk.PhotoImage(img)
        img = Image.open('./icons/Action-arrow-blue-double-down-iconM.png')
        copyImg = ImageTk.PhotoImage(img)
        img = Image.open('./icons/Action-cancel-iconM.png')
        deleteImg = ImageTk.PhotoImage(img)
        img = Image.open('./icons/Action-ok-iconM.png')
        saveImg = ImageTk.PhotoImage(img)
        img = Image.open('./icons/Action-button-info-iconM.png')
        helpImg = ImageTk.PhotoImage(img)

        # distributions list
        Label(self, text='Distributions:').grid(
            row=0, column=0, sticky='nw')
        scrollbarA = Scrollbar(self, orient=VERTICAL)
        scrollbarA.grid(
            row=1, column=1, rowspan=40, sticky='nsw', pady=5)
        self.distLst = Listbox(
            self,
            font=RFONT,
            height=list_height,
            selectmode=SINGLE,
            yscrollcommand=scrollbarA.set)
        self.distLst.bind('<Double-Button-1>', self.show_distribution)
        self.distLst.grid(
            row=1, column=0, rowspan=40, sticky='snew', pady=5)
        scrollbarA['command'] = self.distLst.yview

        # distribution name
        Label(self, text='name').grid(
            row=0, column=3, sticky='snw', padx=10)
        self.distnameEnt = Entry(
            self,
            textvariable=self.distr_name,
            font=RFONT)
        self.distnameEnt.grid(
            row=0, column=4, columnspan=4, sticky='snew')

        # distribution action buttons
        self.daddBtn = Button(
            self,
            image=addImg,
            command=self.add_distribution)
        self.daddBtn.image = addImg
        self.daddBtn.grid(
            row=1, column=2, sticky='sw', padx=10, pady=10)
        self.createToolTip(self.daddBtn, 'add new distribution')

        self.deditBtn = Button(
            self,
            image=editImg,
            command=self.edit_distribution)
        self.deditBtn.image = editImg
        self.deditBtn.grid(
            row=2, column=2, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.deditBtn, 'edit distribution')

        self.dcopyBtn = Button(
            self,
            image=copyImg,
            command=self.copy_distribution)
        self.dcopyBtn.image = copyImg
        self.dcopyBtn.grid(
            row=3, column=2, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.dcopyBtn, 'copy distribution')

        self.ddeleteBtn = Button(
            self,
            image=deleteImg,
            command=self.delete_distribution)
        self.ddeleteBtn.image = deleteImg
        self.ddeleteBtn.grid(
            row=4, column=2, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.ddeleteBtn, 'delete distribution')

        self.dsaveBtn = Button(
            self,
            image=saveImg,
            command=self.insert_or_update_distribution)
        self.dsaveBtn.image = saveImg
        self.dsaveBtn.grid(
            row=5, column=2, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.dsaveBtn, 'save distribution')

        self.helpBtn = Button(
            self,
            image=helpImg,
            command=self.help)
        self.helpBtn.image = helpImg
        self.helpBtn.grid(
            row=6, column=2, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.helpBtn, 'help')

        # details frame
        self.detFrm = LabelFrame(self, text='Distribution details')
        self.detFrm.grid(
            row=1, column=3, rowspan=40,
            columnspan=10, sticky='snew', padx=10, pady=5)

        # grid list
        Label(self.detFrm, text='Grids:').grid(
            row=0, column=0, sticky='nw')
        scrollbarB = Scrollbar(self.detFrm, orient=VERTICAL)
        scrollbarB.grid(
            row=1, column=1, rowspan=40, sticky='nsw')
        self.gridLst = Listbox(
            self.detFrm,
            font=RFONT,
            height=list_height,
            selectmode=SINGLE,
            yscrollcommand=scrollbarB.set)
        self.gridLst.bind('<Double-Button-1>', self.show_grid)
        self.gridLst.grid(
            row=1, column=0, rowspan=40, sticky='snew')
        scrollbarB['command'] = self.gridLst.yview

        # grid action buttons
        self.gaddBtn = Button(
            self.detFrm,
            image=addImg,
            command=self.add_grid)
        self.gaddBtn.image = addImg
        self.gaddBtn.grid(
            row=1, column=2, sticky='sw', padx=10, pady=10)
        self.createToolTip(self.gaddBtn, 'add new grid')

        self.geditBtn = Button(
            self.detFrm,
            image=editImg,
            command=self.edit_grid)
        self.geditBtn.image = editImg
        self.geditBtn.grid(
            row=2, column=2, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.geditBtn, 'edit grid')

        self.gcopyBtn = Button(
            self.detFrm,
            image=copyImg,
            command=self.copy_grid)
        self.gcopyBtn.image = copyImg
        self.gcopyBtn.grid(
            row=3, column=2, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.gcopyBtn, 'copy grid')

        self.gdeleteBtn = Button(
            self.detFrm,
            image=deleteImg,
            command=self.delete_grid)
        self.gdeleteBtn.image = deleteImg
        self.gdeleteBtn.grid(
            row=4, column=2, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.gdeleteBtn, 'delete grid')

        self.gsaveBtn = Button(
            self.detFrm,
            image=saveImg,
            command=self.insert_or_update_grid)
        self.gsaveBtn.image = saveImg
        self.gsaveBtn.grid(
            row=5, column=2, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.gsaveBtn, 'save grid')

        # grid details frame
        self.gridFrm = LabelFrame(
            self.detFrm,
            text='Grid details')
        self.gridFrm.grid(
            row=0, column=3, rowspan=40, columnspan=10,
            sticky='snew', padx=5, pady=10)
        self.gridFrm.columnconfigure(2, minsize=20)
        self.gridFrm.columnconfigure(3, minsize=230)
        self.gridFrm.rowconfigure(8, minsize=250)

        Label(self.gridFrm, text='name').grid(
            row=0, column=0, sticky='snew', padx=5)
        self.gridEnt = Entry(self.gridFrm, width=30)
        self.gridEnt.grid(
            row=1, column=0, columnspan=2, sticky='snew', padx=5, pady=5)

        self.counterLbl = Label(
            self.gridFrm, textvariable=self.counter, font=RFONT)
        self.counterLbl.grid(
            row=2, column=0, columnspan=2, sticky='snew', padx=5, pady=5)

        Label(self.gridFrm, text='library').grid(
            row=3, column=0, sticky='nsw', padx=5, pady=5)
        self.libCbx = Combobox(
            self.gridFrm,
            textvariable=self.library,
            font=RFONT,
            width=10)
        self.libCbx.grid(
            row=3, column=1, sticky='snw', padx=5, pady=5)

        Label(self.gridFrm, text='language').grid(
            row=4, column=0, sticky='nsw', padx=5, pady=5)
        self.langCbx = Combobox(
            self.gridFrm,
            textvariable=self.lang,
            font=RFONT,
            width=10)
        self.langCbx.grid(
            row=4, column=1, sticky='snw', padx=5, pady=5)

        Label(self.gridFrm, text='vendor').grid(
            row=5, column=0, sticky='nsw', padx=5, pady=5)
        self.vendorCbx = Combobox(
            self.gridFrm,
            textvariable=self.vendor,
            font=RFONT,
            width=10)
        self.vendorCbx.grid(
            row=5, column=1, sticky='snw', padx=5, pady=5)

        Label(self.gridFrm, text='audience').grid(
            row=6, column=0, sticky='nsw', padx=5, pady=5)
        self.audnCbx = Combobox(
            self.gridFrm,
            textvariable=self.audn,
            font=RFONT,
            width=10)
        self.audnCbx.grid(
            row=6, column=1, sticky='snw', padx=5, pady=5)

        Label(self.gridFrm, text='mat. type').grid(
            row=7, column=0, sticky='nsw', padx=5, pady=5)
        self.mattypeCbx = Combobox(
            self.gridFrm,
            textvariable=self.mattype,
            font=RFONT,
            width=10)
        self.mattypeCbx.grid(
            row=7, column=1, sticky='snw', padx=5, pady=5)

        # location frame
        self.locFrm = LabelFrame(self.gridFrm, text='Locations')
        self.locFrm.grid(
            row=0, column=3, rowspan=10)
        Label(self.locFrm, text='branch').grid(
            row=0, column=0, sticky='snew', pady=5)
        Label(self.locFrm, text='shelf').grid(
            row=0, column=1, sticky='snew', pady=5)
        Label(self.locFrm, text='qty').grid(
            row=0, column=2, sticky='snew', pady=5)

        # locations canvas
        self.scrollbarC = Scrollbar(self.locFrm, orient=VERTICAL)
        self.scrollbarC.grid(
            row=1, column=3, rowspan=20, sticky='nsw')
        self.locCnv = Canvas(
            self.locFrm,
            width=220,
            height=450,  # find a way to adjust based on preview frm size
            yscrollcommand=self.scrollbarC.set)
        self.locCnv.grid(
            row=2, column=0, columnspan=3, rowspan=20, sticky='snew')
        self.display_frame()

    def display_frame(self):
        self.lf = Frame(self.locCnv)
        self.scrollbarC.config(command=self.locCnv.yview)
        self.locCnv.create_window(
            (0, 0), window=self.lf, anchor="nw",
            tags="self.lf")
        self.lf.bind("<Configure>", self.onFrameConfigure)

    def onFrameConfigure(self, event):
        self.locCnv.config(scrollregion=self.locCnv.bbox('all'))

    def create_loc_widgets(self, rows=1, data=[]):
        for row in range(rows):
            removeBtn = Button(
                self.lf,
                image=self.removeImg)
            removeBtn.image = self.removeImg
            removeBtn.grid(row=row, column=0, sticky='ne', padx=5, pady=2)
            removeBtn['command'] = lambda n=str(removeBtn): self.remove_location(n)

        # distr[str(removeBtn)] = {'distr_id': code['id'],
        #                          'location': location,
        #                          'qty': qty,
        #                          'fund': fund,
        #                          'removeBtn': removeBtn}

            branchCbx = Combobox(self.lf, font=RFONT, width=3)
            branchCbx.grid(
                row=row, column=1, sticky='snew', padx=2, pady=4)
            branchCbx['values'] = sorted(self.branch_idx.values())
            shelfCbx = Combobox(self.lf, font=RFONT, width=3)
            shelfCbx.grid(
                row=row, column=2, sticky='snew', padx=2, pady=4)
            shelfCbx['values'] = sorted(self.shelf_idx.values())
            qtySbx = Spinbox(
                self.lf, font=RFONT, from_=1, to=250, width=3)
            qtySbx.grid(
                row=row, column=3, sticky='snew', padx=2, pady=4)

        add_locationBtn = Button(
            self.lf,
            image=self.addImg,
            command=self.add_location)
        add_locationBtn.image = self.addImg
        add_locationBtn.grid(
            row=row + 1, column=0, sticky='ne', padx=5, pady=2)

    def show_distribution(self, *args):
        pass

    def show_grid(self, *args):
        pass

    def add_distribution(self):
        # allow edits in distribution name box
        enable_widgets([self.distnameEnt])
        self.distr_name.set('')
        self.distr_record = None

        # remove any data from previous lookups
        self.grid_name.set('')
        self.grid_record = None


    def edit_distribution(self):
        pass

    def delete_distribution(self):
        pass

    def insert_or_update_distribution(self):
        if self.distr_name.get():
            if self.distr_record:
                # update
                did = self.distr_record.did
                kwargs = {
                    'name': self.distr_name.get(),
                    'system_id': self.system.get(),
                }
                try:
                    save_data(DistSet, did, **kwargs)
                except BabelError as e:
                    messagebox.showerror('Database error', e)
            else:
                user_id = get_id_from_index(
                    self.profile.get(), self.profile_idx)
                kwargs = {
                    'name': self.distr_name.get(),
                    'system_id': self.system.get(),
                    'user_id': user_id
                }
                try:
                    save_data(DistSet, **kwargs)
                except BabelError as e:
                    messagebox.showerror('Database error', e)


    def copy_distribution(self):
        pass

    def add_grid(self):
        pass

    def edit_grid(self):
        pass

    def delete_grid(self):
        pass

    def insert_or_update_grid(self):
        pass

    def copy_grid(self):
        pass

    def remove_location(self):
        pass

    def add_location(self):
        pass

    def help(self):
        pass

    def display_distributions(self):
        self.distLst.delete(0, END)
        user_id = get_id_from_index(self.profile.get(), self.profile_idx)
        values = get_names(
            DistSet, system_id=self.system.get(), user_id=user_id)
        for v in sorted(values):
            self.distLst.insert(END, v)
    def system_observer(self, *args):
        if self.activeW.get() == 'GridView':
            if self.system.get():
                self.branch_idx = create_code_index(
                    Branch, system_id=self.system.get())
                self.shelf_idx = create_code_index(
                    ShelfCode, system_id=self.system.get())

                # display distributions
                self.display_distributions()

                # re-create location widgets
                self.lf.destroy()
                self.display_frame()
                self.create_loc_widgets()

            if self.system.get() == 1:
                disable_widgets([self.libCbx])
            # elif self.system.get() == 2:
            #     enable_widgets([self.libCbx])

        disable_widgets([self.distnameEnt])

    def observer(self, *args):
        if self.activeW.get() == 'GridView':
            user_data = shelve.open(USER_DATA)
            self.profile.set(user_data['profile'])
            user_data.close()

            # retireve datastore values and id to populate widgets
            # and create a quick reference
            self.audn_idx = create_name_index(Audn)
            self.audnCbx['values'] = sorted(self.audn_idx.values())
            self.lang_idx = create_name_index(Lang)
            self.langCbx['values'] = sorted(self.lang_idx.values())
            self.lib_idx = create_name_index(Library)
            self.libCbx['values'] = sorted(self.lib_idx.values())
            self.mattype_idx = create_name_index(MatType)
            self.mattypeCbx['values'] = sorted(self.mattype_idx.values())
            self.vendor_idx = create_name_index(Vendor)
            self.vendorCbx['values'] = sorted(self.vendor_idx.values())

            if self.system.get():
                self.branch_idx = create_code_index(
                    Branch, system_id=self.system.get())
                self.shelf_idx = create_code_index(
                    ShelfCode, system_id=self.system.get())

            if self.system.get() == 1:
                disable_widgets([self.libCbx])

            elif self.system.get() == 2:
                enable_widgets([self.libCbx])
        disable_widgets([self.distnameEnt])

    def createToolTip(self, widget, text):
        toolTip = ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)
