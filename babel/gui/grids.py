from collections import OrderedDict
import logging
import shelve
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox

from PIL import Image, ImageTk


from errors import BabelError
from data.datastore import (Audn, Branch, DistSet, DistGrid,
                            GridLocation, Lang, Library, MatType,
                            Vendor, ShelfCode)
from gui.data_retriever import (get_names, get_record,
                                delete_data, delete_data_by_did,
                                create_name_index,
                                create_code_index, save_data, save_grid_data)
from gui.fonts import RFONT
from gui.utils import (disable_widgets, enable_widgets, get_id_from_index,
                       ToolTip)
from paths import USER_DATA


mlogger = logging.getLogger('babel_logger')


class GridView(Frame):
    """
    Distribution templates window
    """

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        Frame.__init__(self, parent)
        self.controller = controller
        self.app_data = app_data
        self.activeW = app_data['activeW']
        self.activeW.trace('w', self.observer)
        self.profile = app_data['profile']
        self.profile.trace('w', self.profile_observer)
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
        self.locations = OrderedDict()
        self.delete_locations = []
        self.last_row = 0
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
        self.gridEnt = Entry(
            self.gridFrm, textvariable=self.grid_name, font=RFONT, width=30)
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

    def create_loc_unit(self, loc=(None, '', '', '')):
        unitFrm = Frame(self.lf)
        unitFrm.grid(
            row=self.last_row, column=0, sticky='ne')
        removeBtn = Button(
            unitFrm,
            image=self.removeImg)
        removeBtn.image = self.removeImg
        removeBtn.grid(row=self.last_row, column=0, sticky='ne', padx=5, pady=2)
        removeBtn['command'] = lambda n=removeBtn.winfo_id(): self.remove_location(n)

        branchCbx = Combobox(unitFrm, font=RFONT, width=3)
        branchCbx.grid(
            row=self.last_row, column=1, sticky='snew', padx=2, pady=4)
        branchCbx['values'] = sorted(self.branch_idx.values())
        branchCbx.set(loc[1])
        shelfCbx = Combobox(unitFrm, font=RFONT, width=3)
        shelfCbx.grid(
            row=self.last_row, column=2, sticky='snew', padx=2, pady=4)
        shelfCbx['values'] = sorted(self.shelf_idx.values())
        shelfCbx.set(loc[2])
        qtySbx = Spinbox(
            unitFrm, font=RFONT, from_=1, to=250, width=3)
        qtySbx.grid(
            row=self.last_row, column=3, sticky='snew', padx=2, pady=4)
        qtySbx.set(loc[3])

        gunit = {
            'did': loc[0],
            'parent': unitFrm,
            'removebtn': removeBtn,
            'branchCbx': branchCbx,
            'shelfCbx': shelfCbx,
            'qtySbx': qtySbx
        }

        self.locations[removeBtn.winfo_id()] = gunit

        self.last_row += 1

    def create_loc_widgets(self, locs=[(None, '', '', '')]):
        # reset locations dictionary
        self.locations = OrderedDict()
        self.delete_locations = []
        self.last_row = 0
        for loc in locs:
            self.create_loc_unit(loc)

        self.create_add_locationBtn()

    def create_add_locationBtn(self):
        # class wide accessible add button
        # first try to destroy it
        try:
            self.add_locationBtn.destroy()
        except AttributeError:
            pass

        # rereate in new row
        self.add_locationBtn = Button(
            self.lf,
            image=self.addImg,
            command=self.add_location)
        self.add_locationBtn.image = self.addImg
        self.add_locationBtn.grid(
            row=self.last_row + 1, column=0, sticky='nw', padx=5, pady=2)

    def show_distribution(self, *args):
        name = self.distLst.get(ACTIVE)
        self.distr_name.set(name)
        self.distr_record = get_record(
            DistSet, name=name, system_id=self.system.get())

        self.update_gridLst()

        disable_widgets([self.distnameEnt])

    def show_grid(self, *args):
        self.locations = OrderedDict()
        self.delete_locations = []
        self.last_row = 0
        enable_widgets(self.gridFrm.winfo_children())
        enable_widgets(self.lf.winfo_children())
        self.grid_name.set(self.gridLst.get(ACTIVE))
        self.grid_record = get_record(DistGrid, name=self.grid_name.get())
        self.langCbx.set(self.lang_idx[self.grid_record.lang_id])
        self.vendorCbx.set(self.vendor_idx[self.grid_record.vendor_id])
        self.audnCbx.set(self.audn_idx[self.grid_record.audn_id])
        self.mattypeCbx.set(self.mattype_idx[self.grid_record.matType_id])
        if self.system.get() == 2:
            self.libCbx.set(self.lib_idx[self.grid_record.library_id])

        self.lf.destroy()
        self.display_frame()

        locs = []
        for loc in self.grid_record.gridlocations:
            locs.append((
                loc.did,
                self.branch_idx[loc.branch_id],
                self.shelf_idx[loc.shelfcode_id],
                loc.qty,
            ))
        self.create_loc_widgets(locs)

        disable_widgets(self.gridFrm.winfo_children())
        disable_widgets(self.lf.winfo_children())

    def add_distribution(self):
        # allow edits in distribution name box
        if self.system.get():
            enable_widgets([self.distnameEnt])
            self.distr_name.set('')
            self.distr_record = None

            # remove any data from previous lookups
            self.grid_name.set('')
            self.grid_record = None
            self.gridLst.delete(0, END)

    def edit_distribution(self):
        # enable Entry wid
        if self.distr_name.get():
            enable_widgets([self.distnameEnt])

    def delete_distribution(self):
        if self.distr_record and self.distr_name.get():
            msg = 'Are you sure you want to delete\n{}?'.format(
                str(self.distr_record))
            if messagebox.askokcancel('Deletion', msg):
                mlogger.info('Data for deletion: {}'.format(
                    str(self.distr_record)))
                delete_data(self.distr_record)

                mlogger.debug('Data deleted.')
                self.reset()

            else:
                mlogger.debug('Delection cancelled by user.')

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

            # refresh distributions list
            self.update_distributionLst()
            disable_widgets([self.distnameEnt])

    def copy_distribution(self):
        messagebox.showwarning(
            'Copy Distribution',
            'Please be patient.\nCopying entire distribution feature is under construction.')

    def add_grid(self):
        if self.distr_name.get():
            enable_widgets(self.gridFrm.winfo_children())
            enable_widgets(self.lf.winfo_children())
            self.grid_name.set('')
            self.grid_record = None
            self.recreate_location_widgets()

            if self.system.get() == 1:
                disable_widgets([self.libCbx])

    def edit_grid(self):
        if self.grid_name.get():
            enable_widgets(self.gridFrm.winfo_children())
            enable_widgets(self.lf.winfo_children())

            if self.system.get() == 1:
                disable_widgets([self.libCbx])

    def delete_grid(self):
        if self.grid_record:
            msg = 'Are you sure you want to delete\n{}?'.format(
                str(self.grid_record))
            if messagebox.askokcancel('Deletion', msg):
                mlogger.info('Data for deletion: {}'.format(
                    str(self.grid_record)))
                delete_data(self.grid_record)

                mlogger.debug('Data deleted.')
                self.locations = OrderedDict()
                self.delete_locations = []
                self.last_row = 0
                self.grid_name.set('')
                self.grid_record = None
                self.update_gridLst()

            else:
                mlogger.debug('Delection cancelled by user.')

    def insert_or_update_grid(self):
        if self.distr_record:
            if self.grid_record:
                grid_id = self.grid_record.did
            else:
                grid_id = None

            if self.delete_locations:
                for did in self.delete_locations:
                    delete_data_by_did(GridLocation, did)

            gridlocs = []

            for loc in self.locations.values():
                gridlocs.append(
                    dict(
                        gridloc_id=loc['did'],
                        distgrid_id=grid_id,
                        branch=loc['branchCbx'].get().strip(),
                        shelf=loc['shelfCbx'].get().strip(),
                        qty=loc['qtySbx'].get()
                    )
                )
            try:
                save_grid_data(
                    grid_did=grid_id,
                    name=self.gridEnt.get().strip(),
                    distset_id=self.distr_record.did,
                    library=self.libCbx.get().strip(),
                    lang=self.langCbx.get().strip(),
                    vendor=self.vendorCbx.get().strip(),
                    audn=self.audnCbx.get().strip(),
                    matType=self.mattypeCbx.get().strip(),
                    gridlocs=gridlocs,
                    lib_idx=self.lib_idx,
                    lang_idx=self.lang_idx,
                    vendor_idx=self.vendor_idx,
                    audn_idx=self.audn_idx,
                    mattype_idx=self.mattype_idx,
                    branch_idx=self.branch_idx,
                    shelf_idx=self.shelf_idx,
                )

                self.update_gridLst()
                disable_widgets(self.gridFrm.winfo_children())
                disable_widgets(self.lf.winfo_children())
            except BabelError as e:
                messagebox.showerror('Database Error', e)

    def copy_grid(self):
        messagebox.showwarning(
            'Copy Grid',
            'Please be patient.\nCopying grid feature is under construction.')

    def remove_location(self, n):
        # add removed location to list for deletion
        if self.locations[n]['did']:
            self.delete_locations.append(self.locations[n]['did'])
        self.locations[n]['parent'].destroy()
        self.locations.pop(n, None)
        self.last_row -= 1

    def add_location(self):
        self.add_locationBtn.destroy()
        self.create_loc_unit()
        self.create_add_locationBtn()

    def help(self):
        messagebox.showwarning('Help', 'Under construction..')

    def update_gridLst(self):
        self.gridLst.delete(0, END)
        if self.distr_record:
            values = get_names(
                DistGrid, distset_id=self.distr_record.did)
            for v in sorted(values):
                self.gridLst.insert(END, v)

    def update_distributionLst(self):
        self.distLst.delete(0, END)
        user_id = get_id_from_index(self.profile.get(), self.profile_idx)
        values = get_names(
            DistSet, system_id=self.system.get(), user_id=user_id)
        for v in sorted(values):
            self.distLst.insert(END, v)

    def recreate_location_widgets(self):
        # re-create location widgets
        self.lf.destroy()
        self.display_frame()
        self.create_loc_widgets()

    def reset(self):
        self.distr_name.set('')
        self.grid_name.set('')
        self.library.set('')
        self.lang.set('')
        self.vendor.set('')
        self.audn.set('')
        self.mattype.set('')
        self.distr_record = None
        self.grid_record = None
        self.locations = OrderedDict()
        self.delete_locations = []
        self.last_row = 0
        self.counter.set('')
        self.update_gridLst()
        self.update_distributionLst()
        self.recreate_location_widgets()

        disable_widgets([self.distnameEnt])
        disable_widgets(self.gridFrm.winfo_children())
        disable_widgets(self.lf.winfo_children())

    def profile_observer(self, *args):
        if self.activeW.get() == 'GridView':
            # redo display for new user
            self.reset()
            self.update_distributionLst()

    def system_observer(self, *args):
        if self.activeW.get() == 'GridView':
            if self.system.get():
                self.branch_idx = create_code_index(
                    Branch, system_id=self.system.get())
                self.shelf_idx = create_code_index(
                    ShelfCode, system_id=self.system.get())

                self.reset()

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

                self.update_distributionLst()
                self.recreate_location_widgets()

            if self.system.get() == 1:
                disable_widgets([self.libCbx])

            elif self.system.get() == 2:
                enable_widgets([self.libCbx])
        disable_widgets([self.distnameEnt])
        disable_widgets(self.gridFrm.winfo_children())
        disable_widgets(self.lf.winfo_children())

    def createToolTip(self, widget, text):
        toolTip = ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)
