import logging
import shelve
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox

from PIL import Image, ImageTk


from errors import BabelError
from data.datastore import Resource, Sheet
from gui.fonts import RFONT
from gui.utils import ToolTip
from paths import USER_DATA


mlogger = logging.getLogger('babel_logger')


class ImportView(Frame):
    """
    Sheet import window
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
        list_height = int((self.winfo_screenheight() - 100) / 25)



    def profile_observer(self, *args):
        pass

    def observer(self, *args):
        if self.activeW.get() == 'ImportView':
            pass
