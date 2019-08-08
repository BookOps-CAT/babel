import os
import shelve
import shutil
import sys
from tkinter import *
from tkinter import messagebox, filedialog
from tkinter.ttk import *
from tkinter.ttk import Style
from zipfile import ZipFile

import keyring
from keyring.backends.Windows import WinVaultKeyring
from PIL import Image, ImageTk

p = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, p + '\\' + p.split('\\')[-1])
sys.path.insert(0, p)


from babel import paths
from babel.errors import BabelError
from babel.gui.utils import BusyManager
from babel.credentials import store_in_vault


def prep_space(new_install=False):
    """
    Creates required by Babel folders
    args:
        new_install: Boolean, True - clean from scratch install,
                       False - only app not user data
    """

    # clean up previous installation files & folders
    try:
        shutil.rmtree(paths.APP_DIR)
    except FileNotFoundError:
        pass
    except PermissionError as e:
        raise BabelError(e)

    try:
        if new_install:
            shutil.rmtree(paths.APP_DATA_DIR)
    except FileNotFoundError:
        pass
    except PermissionError as e:
        raise BabelError(e)

    # recreate
    try:
        os.mkdir(paths.APP_DIR)
    except PermissionError as e:
        raise BabelError(e)

    try:
        if new_install:
            os.mkdir(paths.APP_DATA_DIR)
            os.mkdir(os.path.dirname(paths.PROD_LOG_PATH))
    except PermissionError as e:
        raise BabelError(e)


def unpack(zipfile, status_var=None):
    """
    Unzips Babel archive in the temp folder
    args:
        zipfile: str, zip file path
        app_dir: str, created by default in C:/Program Files
        status_var: tkinter StringVar, upacking status msg
    """
    try:

        with ZipFile(zipfile, 'r') as zip:
            if status_var is not None:
                status_var.set('Upacking')
            zip.extractall(paths.APP_DIR)
            if status_var is not None:
                status_var.set('Unpacking complete.')

    except Exception as e:
        raise BabelError(e)


class Installer(Tk):

    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        frm = Frame(self)
        # container.columnconfigure(1, minsize=150)
        frm.grid(padx=20, pady=20)
        # bind shared data between windows
        self.status = StringVar()
        self.update_dir = StringVar()
        self.zipfile = StringVar()
        self.db_host = StringVar()
        self.db_name = StringVar()
        self.db_user = StringVar()
        self.db_passw = StringVar()
        self.db_port = StringVar()

        self.cur_manager = BusyManager(self)

        infoFrm = Frame(frm)
        infoFrm.grid(
            row=0, column=0, sticky='snew', padx=10, pady=10)

        img = Image.open('App-download-manager-icon.png')
        logo = ImageTk.PhotoImage(img)
        logoImg = Label(
            infoFrm, image=logo)
        logoImg.image = logo
        logoImg.grid(
            row=0, column=0, sticky='snew', padx=10, pady=10)

        Label(infoFrm, text='Babel 2 Installer', anchor=CENTER).grid(
            row=1, column=0, sticky='snew', padx=10, pady=10)

        self.statusLbl = Label(
            infoFrm,
            textvariable=self.status,
            anchor=CENTER)
        self.statusLbl.grid(
            row=2, column=0, sticky='snew', padx=10, pady=10)

        dbFrm = LabelFrame(frm, text='Babel database configuration:')
        dbFrm.grid(
            row=0, column=1, sticky='snew', padx=10, pady=10)
        dbFrm.columnconfigure(1, minsize=250)

        Label(dbFrm, text='host:').grid(
            row=0, column=0, sticky='snw', padx=5, pady=3)
        hostEnt = Entry(
            dbFrm,
            textvariable=self.db_host)
        hostEnt.grid(
            row=0, column=1, sticky='snew', padx=5, pady=3)

        Label(dbFrm, text='database:').grid(
            row=1, column=0, sticky='snw', padx=5, pady=3)
        nameEnt = Entry(
            dbFrm,
            textvariable=self.db_name)
        nameEnt.grid(
            row=1, column=1, sticky='snew', padx=5, pady=3)

        Label(dbFrm, text='port:').grid(
            row=2, column=0, sticky='snw', padx=5, pady=3)
        portEnt = Entry(
            dbFrm,
            textvariable=self.db_port)
        portEnt.grid(
            row=2, column=1, sticky='snew', padx=5, pady=3)

        Label(dbFrm, text='user:').grid(
            row=3, column=0, sticky='snw', padx=5, pady=3)
        userEnt = Entry(
            dbFrm,
            textvariable=self.db_user)
        userEnt.grid(
            row=3, column=1, sticky='snew', padx=5, pady=3)

        Label(dbFrm, text='password:').grid(
            row=4, column=0, sticky='snw', padx=5, pady=3)
        passwEnt = Entry(
            dbFrm,
            textvariable=self.db_passw)
        passwEnt.grid(
            row=4, column=1, sticky='snew', padx=5, pady=3)

        btnFrm = Frame(frm)
        btnFrm.grid(
            row=1, column=1, sticky='snew', padx=10, pady=10)

        browseBtn = Button(
            btnFrm,
            text='browse',
            command=self.find_zipfile)
        browseBtn.grid(
            row=0, column=0, sticky='snew', padx=10, pady=10)

        installBtn = Button(
            btnFrm,
            text='install',
            command=self.launch_install)
        installBtn.grid(
            row=0, column=1, sticky='snew', padx=10, pady=10)

        cancelBtn = Button(
            btnFrm,
            text='cancel',
            command=self.destroy)
        cancelBtn.grid(
            row=0, column=2, sticky='snw', padx=10, pady=10)

    def launch_install(self):
        if not self.zipfile.get():
            messagebox.showwarning(
                'Missing input',
                'Please specify Babel zipfile using the Browse button.')
        missing = []
        if not self.db_host.get():
            missing.append('database host')
        if not self.db_port.get():
            missing.append('database port')
        if not self.db_name.get():
            missing.append('database name')
        if not self.db_user.get():
            missing.append('user')
        if not self.db_passw.get():
            missing.append('password')

        if missing:
            missing_str = '\n  -'.join(missing)
            messagebox.showwarning(
                'Input error',
                'Missing database configuration parameters:'
                f'\n  -{missing_str}')
        else:
            try:
                self.cur_manager.busy()
                prep_space(new_install=True)
                unpack(self.zipfile.get(), self.status)

                user_data = shelve.open(paths.USER_DATA)
                user_data['update_dir'] = self.update_dir.get()
                db_config = dict(
                    db_name=self.db_name.get().strip(),
                    host=self.db_host.get().strip(),
                    port=self.db_port.get().strip(),
                    user=self.db_user.get().strip())
                user_data['db_config'] = db_config
                user_data.close()

                store_in_vault(
                    db_config['db_name'],
                    db_config['user'],
                    self.db_passw.get().strip())

                self.cur_manager.notbusy()
                self.status.set('Setup complete.')
                messagebox.showinfo(
                    'Babel setup',
                    'Installation successful.')

            except BabelError as e:
                self.cur_manager.notbusy()
                messagebox.showerror(
                    'Setup error',
                    f'Unable to complete. Error: {e}')

    def find_zipfile(self):
        fh = filedialog.askopenfilename(initialdir=paths.MY_DOCS)
        if fh:
            self.zipfile.set(fh)
            self.update_dir.set(os.path.dirname(self.zipfile.get()))
            self.status.set('zipfile selected...')


if __name__ == '__main__':
    zip_name = 'babel2.zip'
    app_version = 'version.txt'

    # set the backend for credentials
    keyring.set_keyring(WinVaultKeyring())

    app = Installer()
    s = Style()
    s.theme_use('xpnative')
    s.configure('.', font=('device', 12))
    # app.iconbitmap('./icons/babel.ico')
    app.title('Babel Setup')
    app.mainloop()
