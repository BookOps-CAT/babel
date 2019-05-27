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

        

    def system_observer(self, *args):
        user_data = shelve.open(USER_DATA)
        user_data['system'] = self.system.get()
        user_data.close()

    def observer(self, *args):
        if self.activeW.get() == 'FundView':
            self.profile.set('All users')