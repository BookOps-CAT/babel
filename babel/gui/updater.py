# module responsible for handling updates
import logging
from tkinter import *
from tkinter import messagebox, filedialog
from tkinter.ttk import *

from PIL import Image, ImageTk

from errors import BabelError
from gui.utils import BusyManager
from paths import APP_DIR, USER_DATA


mlogger = logging.getLogger('babel_logger')


# this should go to stand-alone updater
def prep_space():
    """
    Creates required by Babel folders
    """

    # clean up previous installation files & folders
    try:
        shutil.rmtree(paths.APP_DIR)
    except FileNotFoundError:
        pass
    except PermissionError as e:
        raise BabelError(e)

    # recreate
    try:
        os.mkdir(paths.APP_DIR)
    except PermissionError as e:
        raise BabelError(e)


class Updater(Tk):

    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        frm = Frame(self)
        frm.grid(padx=20, pady=20)

        infoFrm = Frame(frm)
        infoFrm.grid(
            row=0, column=0, sticky='snew', padx=10, pady=10)

        img = Image.open('./icons/App-download-manager-icon.png')
        logo = ImageTk.PhotoImage(img)
        logoImg = Label(
            infoFrm, image=logo)
        logoImg.image = logo
        logoImg.grid(
            row=0, column=0, sticky='snew', padx=10, pady=10)
