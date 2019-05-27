import logging
import shelve
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox

from PIL import Image, ImageTk


from errors import BabelError
from gui.data_retriever import (get_names, get_record, save_record,
                                delete_records)
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

        self.active_fund = StringVar()

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
        self.fundLst.bind('<Double-Button-1>', self.active_fund)
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

        img = Image.open('./icons/Action-button-info-iconM.png')
        helpImg = ImageTk.PhotoImage(img)
        self.helpBtn = Button(
            self,
            image=helpImg,
            command=self.help)
        self.helpBtn.image = helpImg
        self.helpBtn.grid(
            row=5, column=5, sticky='sw', padx=20, pady=5)

        # details/edit frame
        self.detFrm = Frame(self)
        self.detFrm.grid(
            row=0, column=6, rowspan=40, columnspan=5, sticky='snew')
        Label(self.detFrm, text='out').grid(
            row=0, column=0, columnspan=2, padx=2, sticky='snw')
        Label(self.detFrm, text='in').grid(
            row=0, column=3, columnspan=2, padx=2, sticky='snw')
        Label(self.detFrm, text='out').grid(
            row=0, column=7, columnspan=2, padx=2, sticky='snw')
        Label(self.detFrm, text='in').grid(
            row=0, column=10, columnspan=2, padx=2, sticky='snw')

        # branches
        self.branchesFrm = LabelFrame(self.detFrm, text='Branches')
        self.branchesFrm.grid(
            row=1, column=0, rowspan=10, columnspan=5,
            sticky='snew', padx=5)

        scrollbarB = Scrollbar(self.branchesFrm, orient=VERTICAL)
        scrollbarB.grid(
            row=0, column=1, rowspan=20, sticky='nsw', pady=2)
        self.branchOutLst = Listbox(
            self.branchesFrm,
            font=RFONT,
            height=list_height,
            selectmode=MULTIPLE,
            yscrollcommand=scrollbarB.set)
        self.branchOutLst.bind('<Double-Button-1>', self.add_condition)
        self.branchOutLst.grid(
            row=0, column=0, rowspan=20, sticky='snew', padx=2, pady=2)
        scrollbarB['command'] = self.branchOutLst.yview

        self.branchInBtn = Button(
            self.branchesFrm,
            image=addSImg,
            command=self.add_condition)
        self.branchInBtn.image = addSImg
        self.branchInBtn.grid(
            row=0, column=2, sticky='sw', padx=2, pady=2)

        self.branchOutBtn = Button(
            self.branchesFrm,
            image=removeSImg,
            command=self.remove_condition)
        self.branchOutBtn.image = removeSImg
        self.branchOutBtn.grid(
            row=1, column=2, sticky='sw', padx=2, pady=2)

        scrollbarC = Scrollbar(self.branchesFrm, orient=VERTICAL)
        scrollbarC.grid(
            row=0, column=4, rowspan=20, sticky='nsw', pady=2)
        self.branchInLst = Listbox(
            self.branchesFrm,
            font=RFONT,
            height=list_height,
            selectmode=MULTIPLE,
            yscrollcommand=scrollbarC.set)
        self.branchInLst.bind('<Double-Button-1>', self.remove_condition)
        self.branchInLst.grid(
            row=0, column=3, rowspan=20, sticky='snew', padx=2, pady=2)
        scrollbarC['command'] = self.branchInLst.yview

        # library
        self.libraryFrm = LabelFrame(self.detFrm, text='Library')
        self.libraryFrm.grid(
            row=1, column=7, rowspan=2, columnspan=5,
            sticky='snew', padx=5, pady=5)

        self.libOutLst = Listbox(
            self.libraryFrm,
            font=RFONT,
            height=2,
            selectmode=MULTIPLE)
        self.libOutLst.bind('<Double-Button-1>', self.add_condition)
        self.libOutLst.grid(
            row=0, column=0, rowspan=2, sticky='snew', padx=2, pady=2)

        self.libInBtn = Button(
            self.libraryFrm,
            image=addSImg,
            command=self.add_condition)
        self.libInBtn.image = addSImg
        self.libInBtn.grid(
            row=0, column=1, sticky='sw', padx=5, pady=2)

        self.libOutBtn = Button(
            self.libraryFrm,
            image=removeSImg,
            command=self.remove_condition)
        self.libOutBtn.image = removeSImg
        self.libOutBtn.grid(
            row=1, column=1, sticky='sw', padx=5, pady=2)

        self.libInLst = Listbox(
            self.libraryFrm,
            font=RFONT,
            height=2,
            selectmode=MULTIPLE)
        self.libInLst.bind('<Double-Button-1>', self.remove_condition)
        self.libInLst.grid(
            row=0, column=2, rowspan=2, sticky='snew', padx=2, pady=2)

      # audience
        self.audienceFrm = LabelFrame(self.detFrm, text='Audience')
        self.audienceFrm.grid(
            row=3, column=7, rowspan=3, columnspan=5,
            sticky='snew', padx=5, pady=5)

        self.audnOutLst = Listbox(
            self.audienceFrm,
            font=RFONT,
            height=3,
            selectmode=MULTIPLE)
        self.audnOutLst.bind('<Double-Button-1>', self.add_condition)
        self.audnOutLst.grid(
            row=0, column=0, rowspan=2, sticky='snew', padx=2, pady=2)

        self.audnInBtn = Button(
            self.audienceFrm,
            image=addSImg,
            command=self.add_condition)
        self.audnInBtn.image = addSImg
        self.audnInBtn.grid(
            row=0, column=1, sticky='sw', padx=5, pady=2)

        self.audnOutBtn = Button(
            self.audienceFrm,
            image=removeSImg,
            command=self.remove_condition)
        self.audnOutBtn.image = removeSImg
        self.audnOutBtn.grid(
            row=1, column=1, sticky='sw', padx=5, pady=2)

        self.audnInLst = Listbox(
            self.audienceFrm,
            font=RFONT,
            height=2,
            selectmode=MULTIPLE)
        self.audnInLst.bind('<Double-Button-1>', self.remove_condition)
        self.audnInLst.grid(
            row=0, column=2, rowspan=2, sticky='snew', padx=2, pady=2)

      # material type
        self.mattypeFrm = LabelFrame(self.detFrm, text='Material type')
        self.mattypeFrm.grid(
            row=6, column=7, rowspan=3, columnspan=5,
            sticky='snew', padx=5, pady=5)

        self.mattypeOutLst = Listbox(
            self.mattypeFrm,
            font=RFONT,
            height=3,
            selectmode=MULTIPLE)
        self.mattypeOutLst.bind('<Double-Button-1>', self.add_condition)
        self.mattypeOutLst.grid(
            row=0, column=0, rowspan=2, sticky='snew', padx=2, pady=2)

        self.mattypeInBtn = Button(
            self.mattypeFrm,
            image=addSImg,
            command=self.add_condition)
        self.mattypeInBtn.image = addSImg
        self.mattypeInBtn.grid(
            row=0, column=1, sticky='sw', padx=5, pady=2)

        self.mattypeOutBtn = Button(
            self.mattypeFrm,
            image=removeSImg,
            command=self.remove_condition)
        self.mattypeOutBtn.image = removeSImg
        self.mattypeOutBtn.grid(
            row=1, column=1, sticky='sw', padx=5, pady=2)

        self.mattypeInLst = Listbox(
            self.mattypeFrm,
            font=RFONT,
            height=2,
            selectmode=MULTIPLE)
        self.mattypeInLst.bind('<Double-Button-1>', self.remove_condition)
        self.mattypeInLst.grid(
            row=0, column=2, rowspan=2, sticky='snew', padx=2, pady=2)

    def add_data(self):
        pass

    def edit_data(self):
        pass

    def delete_data(self):
        pass

    def insert_or_update_data(self):
        pass

    def help(self):
        pass

    def select_library(self):
        pass

    def add_condition(self):
        pass

    def remove_condition(self):
        pass

    def system_observer(self, *args):
        user_data = shelve.open(USER_DATA)
        user_data['system'] = self.system.get()
        user_data.close()
        if self.system.get() == 1:
            # show BPL funds
            print('BPL')
        if self.system.get() == 2:
            print('NYPL')

    def observer(self, *args):
        if self.activeW.get() == 'FundView':
            self.profile.set('All users')