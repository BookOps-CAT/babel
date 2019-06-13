from tkinter import *
from tkinter.ttk import *
import shelve

from PIL import Image, ImageTk


from data.datastore import User
from gui.data_retriever import get_names, create_name_index
from gui.home import HomeView
from gui.reports import ReportView
from gui.tables import TableView
from gui.funds import FundView
from gui.grids import GridView
from gui.ingest import ImportView
from gui.carts import CartsView
from gui.cart import CartView
from paths import USER_DATA


class Base(Tk):

    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        # use in prod
        w, h = self.winfo_screenwidth() - 100, self.winfo_screenheight() - 100
        self.geometry("%dx%d+80+0" % (w, h))

        # container where frames are stacked
        container = Frame(self)
        container.columnconfigure(1, minsize=150)
        container.grid(padx=10)
        # bind shared data between windows
        self.activeW = StringVar()
        self.profile = StringVar()
        self.profile.trace('w', self.profile_observer)
        self.system = IntVar()  # BPL 1, NYPL 2
        self.system.trace('w', self.system_observer)
        self.active_id = IntVar()

        img = Image.open('./icons/App-personal-icon.png')
        profileImg = ImageTk.PhotoImage(img)
        profile = Menubutton(container, image=profileImg)
        profile.grid(row=0, column=0, sticky='nw')
        profile.image = profileImg

        self.profileLbl = Label(container, textvariable=self.profile)
        self.profileLbl.grid(row=0, column=1, columnspan=3, sticky='snw')

        profile.menu = Menu(profile, tearoff=0)
        profile["menu"] = profile.menu

        # pull from datastore as tuple(did, name)
        users = get_names(User)
        users.insert(0, 'All users')
        for name in users:
            profile.menu.add_radiobutton(
                label=name,
                variable=self.profile,
                value=name)

        systemLbl = Label(container, text='System:')
        systemLbl.grid(row=0, column=4, sticky='snw')

        bplBtn = Radiobutton(
            container, text='BPL', variable=self.system, value=1)
        bplBtn.grid(
            row=0, column=5, sticky='snw')
        nypBtn = Radiobutton(
            container, text='NYPL', variable=self.system, value=2)
        nypBtn.grid(
            row=0, column=6, sticky='snw')

        self.state = False
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.end_fullscreen)

        Separator(container, orient=HORIZONTAL).grid(
            row=1, column=0, columnspan=7, sticky='snew')

        # set up menu bar
        menubar = Menu(self)
        navig_menu = Menu(menubar, tearoff=0)
        navig_menu.add_command(
            label='Home',
            command=lambda: self.show_frame('HomeView'))
        navig_menu.add_command(
            label='Import',
            command=lambda: self.show_frame('ImportView'))
        navig_menu.add_command(
            label='Carts',
            command=lambda: self.show_frame('CartsView'))
        navig_menu.add_command(
            label='Reports',
            command=None)
        navig_menu.add_command(
            label='Search',
            command=None)
        navig_menu.add_command(
            label='Grids',
            command=lambda: self.show_frame('GridView'))
        navig_menu.add_command(
            label='Funds',
            command=lambda: self.show_frame('FundView'))
        navig_menu.add_command(
            label='Tables',
            command=lambda: self.show_frame('TableView'))
        navig_menu.add_command(
            label='Settings',
            command=None)

        navig_menu.add_separator()
        navig_menu.add_command(label='Exit', command=self.quit)
        menubar.add_cascade(label='Menu', menu=navig_menu)

        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label='Help index', command=None)
        help_menu.add_command(label='Updates', command=None)
        help_menu.add_separator()
        help_menu.add_command(label='About',
                              command=None)
        menubar.add_cascade(label='Help', menu=help_menu)

        self.config(menu=menubar)

        # profiles index for quick reference
        self.profile_idx = create_name_index(User)

        # profile & system
        user_data = shelve.open(USER_DATA)
        try:
            self.profile.set(user_data['profile'])
            self.system.set(user_data['system'])
        except KeyError:
            pass
        user_data.close()

        # create icons and share them among widgets
        img = Image.open('./icons/Action-edit-add-iconM.png')
        addImg = ImageTk.PhotoImage(img)
        img = Image.open('./icons/Action-reload-iconM.png')
        editImg = ImageTk.PhotoImage(img)
        img = Image.open('./icons/Action-cancel-iconM.png')
        deleteImg = ImageTk.PhotoImage(img)
        img = Image.open('./icons/Action-ok-iconM.png')
        saveImg = ImageTk.PhotoImage(img)
        img = Image.open('./icons/Action-ok-iconS.png')
        saveImgS = ImageTk.PhotoImage(img)
        img = Image.open('./icons/Action-button-info-iconM.png')
        helpImg = ImageTk.PhotoImage(img)
        img = Image.open('./icons/Action-arrow-blue-double-down-iconM.png')
        copyImg = ImageTk.PhotoImage(img)
        img = Image.open('./icons/Action-arrow-blue-double-down-iconS.png')
        copyImgS = ImageTk.PhotoImage(img)
        img = Image.open('./icons/Action-viewmag-iconM.png')
        viewImg = ImageTk.PhotoImage(img)
        img = Image.open('./icons/App-floppy-iconM.png')
        marcImg = ImageTk.PhotoImage(img)
        img = Image.open('./icons/App-spreadsheet-iconM.png')
        sheetImg = ImageTk.PhotoImage(img)
        img = Image.open('./icons/App-proxy-iconM.png')
        linkImg = ImageTk.PhotoImage(img)
        img = Image.open('./icons/Action-arrow-blue-left-iconS.png')
        previousImg = ImageTk.PhotoImage(img)
        img = Image.open('./icons/Action-arrow-blue-right-iconS.png')
        nextImg = ImageTk.PhotoImage(img)
        img = Image.open('./icons/Action-arrow-blue-double-left-iconS.png')
        startImg = ImageTk.PhotoImage(img)
        img = Image.open('./icons/Action-arrow-blue-double-right-iconS.png')
        endImg = ImageTk.PhotoImage(img)
        img = Image.open('./icons/App-browser-iconM.png')
        sierraImg = ImageTk.PhotoImage(img)
        img = Image.open('./icons/Action-cancel-iconS.png')
        deleteImgS = ImageTk.PhotoImage(img)
        img = Image.open('./icons/Action-reload-iconS.png')
        editImgS = ImageTk.PhotoImage(img)
        img = Image.open('./icons/App-develop-iconS.png')
        notFoundImg = ImageTk.PhotoImage(img)
        img = Image.open('./icons/App-konqueror-iconS.png')
        foundImg = ImageTk.PhotoImage(img)
        img = Image.open('./icons/Action-edit-add-iconS.png')
        addImgS = ImageTk.PhotoImage(img)

        self.app_data = {
            'activeW': self.activeW,
            'profile': self.profile,
            'profile_idx': self.profile_idx,
            'system': self.system,
            'active_id': self.active_id,
            'img': {
                'add': addImg,
                'edit': editImg,
                'delete': deleteImg,
                'save': saveImg,
                'saveS': saveImgS,
                'help': helpImg,
                'copy': copyImg,
                'copyS': copyImgS,
                'view': viewImg,
                'marc': marcImg,
                'sheet': sheetImg,
                'link': linkImg,
                'previous': previousImg,
                'next': nextImg,
                'start': startImg,
                'end': endImg,
                'sierra': sierraImg,
                'deleteS': deleteImgS,
                'editS': editImgS,
                'notfound': notFoundImg,
                'found': foundImg,
                'addS': addImgS}}

        # spawn Babel frames
        self.frames = {}
        for F in (FundView, GridView, HomeView, ReportView, TableView,
                  ImportView, CartsView, CartView):
            page_name = F.__name__
            frame = F(parent=container, controller=self,
                      **self.app_data)
            self.frames[page_name] = frame

            # put all windows in the same location
            frame.grid(
                row=1, column=0, columnspan=20, sticky='snew', padx=5, pady=5)

        # lift to the top main window
        self.show_frame('HomeView')

    def show_frame(self, page_name):
        """show frame for the given page name"""

        frame = self.frames[page_name]
        # set tier for behavioral control
        self.activeW.set(page_name)
        frame.tkraise()

    def profile_observer(self, *args):
        if self.profile.get() != 'All users':
            user_data = shelve.open(USER_DATA)
            user_data['profile'] = self.profile.get()
            user_data.close()

    def system_observer(self, *args):
        user_data = shelve.open(USER_DATA)
        user_data['system'] = self.system.get()
        user_data.close()

    def toggle_fullscreen(self, event=None):
        self.state = not self.state  # Just toggling the boolean
        self.attributes("-fullscreen", self.state)
        return "break"

    def end_fullscreen(self, event=None):
        self.state = False
        self.attributes("-fullscreen", False)
        return "break"
