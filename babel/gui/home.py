from tkinter import *
from tkinter.ttk import *

from PIL import Image, ImageTk


# from gui.utils import BusyManager, ToolTip


class HomeView(Frame):

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        Frame.__init__(self, parent)
        self.controller = controller
        self.app_data = app_data
        self.profile = self.app_data['profile']
        self.activeW = app_data['activeW']
        self.activeW.trace('w', self.observer)

        img = Image.open('./icons/App-ark-iconL.png')
        importImg = ImageTk.PhotoImage(img)
        self.importBtn = Button(
            self,
            # style='Regular.TButton',
            image=importImg,
            compound=TOP,
            text='Import',
            command=lambda: controller.show_frame('ImportView'))
        self.importBtn.image = importImg
        self.importBtn.grid(
            row=1, column=0, sticky='sw', padx=20, pady=10)

        img = Image.open('./icons/App-wood-box-icon.png')
        cartImg = ImageTk.PhotoImage(img)
        self.cartBtn = Button(
            self,
            # style='Regular.TButton',
            image=cartImg,
            compound=TOP,
            text='Cart',
            command=None)
        self.cartBtn.image = cartImg
        self.cartBtn.grid(
            row=1, column=1, sticky='sw', padx=20, pady=10)

        img = Image.open('./icons/App-floppy-icon.png')
        exportImg = ImageTk.PhotoImage(img)
        self.exportBtn = Button(
            self,
            # style='Regular.TButton',
            image=exportImg,
            compound=TOP,
            text='Export',
            command=None)
        self.exportBtn.image = exportImg
        self.exportBtn.grid(
            row=1, column=2, sticky='sw', padx=20, pady=10)

        img = Image.open('./icons/Action-find-icon.png')
        searchImg = ImageTk.PhotoImage(img)
        self.searchBtn = Button(
            self,
            # style='Regular.TButton',
            image=searchImg,
            compound=TOP,
            text='Search',
            command=None)
        self.searchBtn.image = searchImg
        self.searchBtn.grid(
            row=1, column=3, sticky='sw', padx=20, pady=10)

        img = Image.open('./icons/App-ksirtet-icon.png')
        gridImg = ImageTk.PhotoImage(img)
        self.gridBtn = Button(
            self,
            # style='Regular.TButton',
            image=gridImg,
            compound=TOP,
            text='Grids',
            command=lambda: controller.show_frame('GridView'))
        self.gridBtn.image = gridImg
        self.gridBtn.grid(
            row=2, column=0, sticky='sw', padx=20, pady=10)

        img = Image.open('./icons/App-kgoldrunner-gold-icon.png')
        fundImg = ImageTk.PhotoImage(img)
        self.fundBtn = Button(
            self,
            # style='Regular.TButton',
            image=fundImg,
            compound=TOP,
            text='Funds',
            command=lambda: controller.show_frame('FundView'))
        self.fundBtn.image = fundImg
        self.fundBtn.grid(
            row=2, column=1, sticky='sw', padx=20, pady=10)

        img = Image.open('./icons/App-chart-icon.png')
        reportsImg = ImageTk.PhotoImage(img)
        self.reportsBtn = Button(
            self,
            # style='Regular.TButton',
            image=reportsImg,
            compound=TOP,
            text='Reports',
            command=None)
        self.reportsBtn.image = reportsImg
        self.reportsBtn.grid(
            row=2, column=2, sticky='sw', padx=20, pady=10)

        img = Image.open('./icons/App-database-icon.png')
        dbImg = ImageTk.PhotoImage(img)
        self.dbBtn = Button(
            self,
            # style='Regular.TButton',
            image=dbImg,
            compound=TOP,
            text='Tables',
            command=lambda: controller.show_frame('TableView'))
        self.dbBtn.image = dbImg
        self.dbBtn.grid(
            row=2, column=3, sticky='sw', padx=20, pady=10)

        img = Image.open('./icons/Action-run-icon.png')
        settingsImg = ImageTk.PhotoImage(img)
        self.settingsBtn = Button(
            self,
            # style='Regular.TButton',
            image=settingsImg,
            compound=TOP,
            text='Settings',
            command=None)
        self.settingsBtn.image = settingsImg
        self.settingsBtn.grid(
            row=3, column=0, sticky='sw', padx=20, pady=10)

    def observer(self, *args):
        if self.activeW.get() == 'MainView':
            user_data = shelve.open(USER_DATA)
            self.profile.set(user_data['profile'])
            user_data.close()
