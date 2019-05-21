from tkinter import *
from tkinter.ttk import *

from PIL import Image, ImageTk

from gui.home import HomeView
from gui.reports import ReportView
from gui.tables import TableView


class Base(Tk):

    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        # use in prod
        # w, h = self.winfo_screenwidth(), self.winfo_screenheight()
        # self.geometry("%dx%d+0+0" % (w, h))

        # container where frames are stacked
        container = Frame(self)
        container.columnconfigure(2, minsize=20)
        container.grid()
        # bind shared data between windows
        self.activeW = StringVar()
        self.profile = StringVar()
        self.system = IntVar()  # BPL 1, NYPL 2

        # temp, pull from db instead
        users = [('ALL', 0), ('Libbhy', 1), ('Alex', 2), ('Scott', 3)]

        img = Image.open('./icons/App-personal-icon.png')
        profileImg = ImageTk.PhotoImage(img)
        profile = Menubutton(container, image=profileImg)
        profile.grid(row=0, column=0, sticky='nw')
        profile.image = profileImg

        self.profileLbl = Label(container, textvariable=self.profile)
        self.profileLbl.grid(row=0, column=1, columnspan=20, sticky='snw')

        profile.menu = Menu(profile, tearoff=0)
        profile["menu"] = profile.menu

        for name, uid in users:
            profile.menu.add_radiobutton(
                label=name,
                variable=self.profile,
                value=name)

        systemLbl = Label(container, text='System:')
        systemLbl.grid(row=0, column=3, sticky='sne')

        bplBtn = Radiobutton(
            container, text='BPL', variable=self.system, value=1)
        bplBtn.grid(
            row=0, column=4, sticky='sne')
        nypBtn = Radiobutton(
            container, text='NYPL', variable=self.system, value=2)
        nypBtn.grid(
            row=0, column=5, sticky='snw')

        self.state = False
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.end_fullscreen)

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
            command=None)
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

        # retrieve current profile from user_data and set below
        # !!!! code needed
        self.profile.set('ALL')
        self.app_data = {
            'activeW': self.activeW,
            'profile': self.profile,
            'system': self.system}

        # spawn Babel frames
        self.frames = {}
        for F in (HomeView, ReportView, TableView):
            page_name = F.__name__
            frame = F(parent=container, controller=self,
                      **self.app_data)
            self.frames[page_name] = frame

            # put all windows in the same location
            frame.grid(row=1, column=0, columnspan=20, sticky='snew', padx=5, pady=5)

        # lift to the top main window
        self.show_frame('HomeView')

    def show_frame(self, page_name):
        """show frame for the given page name"""

        frame = self.frames[page_name]
        # set tier for behavioral control
        self.activeW.set(page_name)
        frame.tkraise()

    def toggle_fullscreen(self, event=None):
        self.state = not self.state  # Just toggling the boolean
        self.attributes("-fullscreen", self.state)
        return "break"

    def end_fullscreen(self, event=None):
        self.state = False
        self.attributes("-fullscreen", False)
        return "break"
