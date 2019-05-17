from tkinter import *
from tkinter.ttk import *

from PIL import Image, ImageTk

from gui.home import HomeView
from gui.reports import ReportView


class Base(Tk):

    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)
        w, h = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry("%dx%d+0+0" % (w, h))

        # container where frames are stacked
        container = Frame(self)
        container.grid()

        self.state = False
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.end_fullscreen)

        # bind shared data between windows
        self.activeW = StringVar()
        self.app_data = {'activeW': self.activeW}

        # spawn Babel frames
        self.frames = {}
        for F in (HomeView, ReportView):
            page_name = F.__name__
            frame = F(parent=container, controller=self,
                      **self.app_data)
            self.frames[page_name] = frame

            # put all windows in the same location
            frame.grid(row=0, column=0, sticky='snew', padx=10, pady=10)

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
            command=None)
        navig_menu.add_command(
            label='Reports',
            command=None)
        navig_menu.add_command(
            label='Settings',
            command=None)

        navig_menu.add_separator()
        navig_menu.add_command(label='Exit', command=self.quit)
        menubar.add_cascade(label='Menu', menu=navig_menu)
        # report_menu = Menu(menubar, tearoff=0)
        # report_menu.add_command(
        #     label='Reports', command=None)
        # menubar.add_cascade(label='Reports', menu=report_menu)
        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label='Help index', command=None)
        help_menu.add_command(label='Updates', command=None)
        help_menu.add_separator()
        help_menu.add_command(label='About',
                              command=None)
        menubar.add_cascade(label='Help', menu=help_menu)

        # profile
        # profile_menu = Menu(menubar, tearoff=0)
        img = Image.open('./icons/Everaldo-Crystal-Clear-App-personal.ico')
        profileImg = ImageTk.PhotoImage(img)
        # profile_menu.add_command(image=profileImg)
        menubar.add_command(
            bitmap=profileImg,
            command=None)
        # profile_menu.image = profileImg

        self.config(menu=menubar)

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
