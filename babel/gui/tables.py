from tkinter import *
from tkinter.ttk import *

from PIL import Image, ImageTk


class TableView(Frame):
    """
    Shared among settings widgets frame
    """

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        Frame.__init__(self, parent)
        self.controller = controller
        self.app_data = app_data
        self.profile = app_data['profile']
        self.system = app_data['system']
        self.gen_list = StringVar()
        self.det_list = StringVar()

        # layout
        self.columnconfigure(0, minsize=200) # genLst col
        self.columnconfigure(2, minsize=5)
        self.columnconfigure(3, minsize=200) # detLst col

        # tables list
        Label(self, text='Tables:').grid(
            row=0, column=0, sticky='nw')
        scrollbarA = Scrollbar(self, orient=VERTICAL)
        scrollbarA.grid(
            row=1, column=1, rowspan=20, sticky='nsw')
        self.genLst = Listbox(
            self,
            yscrollcommand=scrollbarA.set)
        self.genLst.bind('<Double-Button-1>', self.populate_detail_list)
        self.genLst.grid(
            row=1, column=0, rowspan=20, sticky='snew')
        scrollbarA['command'] = self.genLst.yview

        # table values list
        self.detLbl = Label(self, textvariable=self.det_list)
        self.detLbl.grid(
            row=0, column=3, sticky='nw')
        scrollbarB = Scrollbar(self, orient=VERTICAL)
        scrollbarB.grid(
            row=1, column=4, rowspan=20, sticky='nsw')
        self.detLst = Listbox(
            self,
            yscrollcommand=scrollbarB.set)
        self.detLst.bind('<Double-Button-1>', self.populate_detail_list)
        self.detLst.grid(
            row=1, column=3, rowspan=20, sticky='snew')
        scrollbarB['command'] = self.detLst.yview

        # action buttons
        img = Image.open('./icons/Action-edit-add-iconM.png')
        addImg = ImageTk.PhotoImage(img)
        self.addBtn = Button(
            self,
            # style='Regular.TButton',
            image=addImg,
            # compound=TOP,
            # text='new',
            command=None)
        self.addBtn.image = addImg
        self.addBtn.grid(
            row=1, column=5, sticky='sw', padx=20, pady=10)

        img = Image.open('./icons/Action-reload-iconM.png')
        editImg = ImageTk.PhotoImage(img)
        self.editBtn = Button(
            self,
            # style='Regular.TButton',
            image=editImg,
            # compound=TOP,
            # text='new',
            command=None)
        self.editBtn.image = editImg
        self.editBtn.grid(
            row=2, column=5, sticky='sw', padx=20, pady=5)

        img = Image.open('./icons/Action-cancel-iconM.png')
        deleteImg = ImageTk.PhotoImage(img)
        self.deleteBtn = Button(
            self,
            # style='Regular.TButton',
            image=deleteImg,
            # compound=TOP,
            # text='new',
            command=None)
        self.deleteBtn.image = deleteImg
        self.deleteBtn.grid(
            row=3, column=5, sticky='sw', padx=20, pady=5)

        img = Image.open('./icons/Action-ok-iconM.png')
        saveImg = ImageTk.PhotoImage(img)
        self.saveBtn = Button(
            self,
            # style='Regular.TButton',
            image=saveImg,
            # compound=TOP,
            # text='new',
            command=None)
        self.saveBtn.image = saveImg
        self.saveBtn.grid(
            row=4, column=5, sticky='sw', padx=20, pady=5)

    def populate_detail_list(self):
        print('populating')

