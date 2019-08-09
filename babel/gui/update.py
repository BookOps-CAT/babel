# module responsible for handling updates
import logging
import os
import shelve
import subprocess
from tkinter import *
from tkinter import filedialog
from tkinter.ttk import *

from PIL import Image, ImageTk

from logging_settings import format_traceback
from paths import USER_DATA, MY_DOCS, APP_DIR


mlogger = logging.getLogger('babel_logger')


class UpdateWidget:

    def __init__(self, parent, remote_version):
        self.parent = parent
        if remote_version:
            version_msg = f'A new version {remote_version} was found.'
        else:
            version_msg = ('Unable to find update directory\n'
                           'Please click "browse" to find correct location.')

        top = self.top = Toplevel(master=self.parent)
        top.title('Updater')

        frm = Frame(self.top)
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

        btnFrm = Frame(frm)
        btnFrm.grid(
            row=0, column=1, stick='snew', padx=10, pady=10)

        Label(
            btnFrm,
            text=version_msg).grid(
            row=0, column=0, columnspan=3, sticky='snw', padx=10, pady=10)

        Label(
            btnFrm,
            text='Select "browse" to apply specific Babel update.\n'
                 'Select "install" run automatic update.\n'
                 'Select "cancel" to skip.').grid(
            row=1, column=0, columnspan=3, sticky='snw', padx=10, pady=20)

        browseBtn = Button(
            btnFrm,
            text='browse',
            command=self.find_update)
        browseBtn.grid(
            row=2, column=0, sticky='snew', padx=10, pady=10)

        installBtn = Button(
            btnFrm,
            text='install',
            command=self.launch_update)
        installBtn.grid(
            row=2, column=1, sticky='snew', padx=10, pady=10)

        cancelBtn = Button(
            btnFrm,
            text='cancel',
            command=self.top.destroy)
        cancelBtn.grid(
            row=2, column=2, sticky='snew', padx=10, pady=10)

    def launch_update(self):
        user_data = shelve.open(USER_DATA)
        if 'update_dir' in user_data:
            update_dir = user_data['update_dir']
        else:
            update_dir = None
        user_data.close()

        if update_dir:

            try:

                args = '{} "{}" "{}"'.format(
                    'updater.exe', update_dir, APP_DIR)
                CREATE_NO_WINDOW = 0x08000000
                subprocess.call(args, creationflags=CREATE_NO_WINDOW)

            except Exception as exc:
                _, _, exc_traceback = sys.exc_info()
                tb = format_traceback(exc, exc_traceback)
                mlogger.error(
                    'Unhandled error on Babel update.'
                    f'Traceback: {tb}')

    def find_update(self):
        fh = filedialog.askopenfilename(initialdir=MY_DOCS)
        if fh:
            user_data = shelve.open(USER_DATA)
            user_data['update_dir'] = os.path.dirname(fh)
            user_data.close()
            # self.launch_update()
