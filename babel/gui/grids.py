import logging
import shelve
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox

from PIL import Image, ImageTk


from errors import BabelError
from data.datastore import (Audn, Branch, Library, MatType)
from gui.data_retriever import (get_codes, get_names, get_record,
                                delete_data)
from gui.fonts import RFONT
from gui.utils import disable_widgets, enable_widgets, ToolTip
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
        self.system = app_data['system']
        self.system.trace('w', self.system_observer)
        list_height = int((self.winfo_screenheight() - 100) / 25)

        # local variables
        self.distr_name = StringVar()

        # distributions list
        Label(self, text='Distributions:').grid(
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
        self.fundLst.bind('<Double-Button-1>', self.show_distribution)
        self.fundLst.grid(
            row=1, column=0, rowspan=40, sticky='snew')
        scrollbarA['command'] = self.fundLst.yview

        # action buttons
        img = Image.open('./icons/Action-edit-add-iconM.png')
        addImg = ImageTk.PhotoImage(img)
        self.addBtn = Button(
            self,
            image=addImg,
            command=self.add_distribution)
        self.addBtn.image = addImg
        self.addBtn.grid(
            row=1, column=5, sticky='sw', padx=10, pady=10)
        self.createToolTip(self.addBtn, 'add new')

        img = Image.open('./icons/Action-reload-iconM.png')
        editImg = ImageTk.PhotoImage(img)
        self.editBtn = Button(
            self,
            image=editImg,
            command=self.edit_distribution)
        self.editBtn.image = editImg
        self.editBtn.grid(
            row=2, column=5, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.editBtn, 'edit')

        img = Image.open('./icons/Action-arrow-blue-double-down-iconM.png')
        copyImg = ImageTk.PhotoImage(img)
        self.copyBtn = Button(
            self,
            image=copyImg,
            command=self.copy_distribution)
        self.copyBtn.image = copyImg
        self.copyBtn.grid(
            row=3, column=5, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.copyBtn, 'copy')

        img = Image.open('./icons/Action-cancel-iconM.png')
        deleteImg = ImageTk.PhotoImage(img)
        self.deleteBtn = Button(
            self,
            image=deleteImg,
            command=self.delete_distribution)
        self.deleteBtn.image = deleteImg
        self.deleteBtn.grid(
            row=4, column=5, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.deleteBtn, 'delete')

        img = Image.open('./icons/Action-ok-iconM.png')
        saveImg = ImageTk.PhotoImage(img)
        self.saveBtn = Button(
            self,
            image=saveImg,
            command=self.insert_or_update_distribution)
        self.saveBtn.image = saveImg
        self.saveBtn.grid(
            row=5, column=5, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.saveBtn, 'save')

        img = Image.open('./icons/Action-button-info-iconM.png')
        helpImg = ImageTk.PhotoImage(img)
        self.helpBtn = Button(
            self,
            image=helpImg,
            command=self.help)
        self.helpBtn.image = helpImg
        self.helpBtn.grid(
            row=6, column=5, sticky='sw', padx=10, pady=5)
        self.createToolTip(self.helpBtn, 'help')

        # details frame
        self.detFrm = LabelFrame(self, text='Distribution details')
        self.detFrm.grid(
            row=1, column=6, rowspan=40, columnspan=5, sticky='snew')

        Label(self.detFrm, text='name:').grid(
            row=0, column=0, sticky='snw')
        self.distrEnt = Entry(
            self.detFrm,
            font=RFONT,
            textvariable=self.distr_name)
        self.distrEnt.grid(
            row=0, column=1, columnspan=3, sticky='snew')

        # grids frame
        self.gridFrm = Frame(self.detFrm)
        self.gridFrm.grid(
            row=1, column=0, sticky='snew')

        # notebook with tabs
        self.gridNtb = Notebook(
            self.gridFrm,
            style='lefttab.TNotebook')
        self.gridNtb.grid(
            row=0, column=0, sticky='snew')
        tabs_data = self.tabs_data()
        self.create_tabs(tabs_data)

    def tabs_data(self):
        return ['grid A', 'grid B', 'grid C']

    def create_tabs(self, data):
        for d in data:
            f = Frame(self.gridNtb)
            self.gridNtb.add(f, text=d)

    def show_distribution(self, *args):
        pass

    def add_distribution(self):
        pass

    def edit_distribution(self):
        pass

    def delete_distribution(self):
        pass

    def insert_or_update_distribution(self):
        pass

    def copy_distribution(self):
        pass

    def help(self):
        pass

    def system_observer(self, *args):
        pass

    def observer(self, *args):
        pass

    def createToolTip(self, widget, text):
        toolTip = ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)
