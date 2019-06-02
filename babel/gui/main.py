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
            command=None)
        navig_menu.add_command(
            label='Carts',
            command=None)
        navig_menu.add_command(
            label='Search',
            command=None)
        navig_menu.add_command(
            label='Export',
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
            label='Reports',
            command=None)
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

        # profile
        user_data = shelve.open(USER_DATA)
        self.profile.set(user_data['profile'])
        user_data.close()

        self.profile.set('All users')
        self.app_data = {
            'activeW': self.activeW,
            'profile': self.profile,
            'profile_idx': self.profile_idx,
            'system': self.system}

        # spawn Babel frames
        self.frames = {}
        for F in (FundView, GridView, HomeView, ReportView, TableView):
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

    def toggle_fullscreen(self, event=None):
        self.state = not self.state  # Just toggling the boolean
        self.attributes("-fullscreen", self.state)
        return "break"

    def end_fullscreen(self, event=None):
        self.state = False
        self.attributes("-fullscreen", False)
        return "break"
