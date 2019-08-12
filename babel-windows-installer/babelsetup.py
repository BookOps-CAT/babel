import os
import shelve
import shutil
from tkinter import *
from tkinter import messagebox, filedialog
from tkinter.ttk import *
from tkinter.ttk import Style
from zipfile import ZipFile

import keyring
from keyring.backends.Windows import WinVaultKeyring
from PIL import Image, ImageTk


APP_DIR = 'C:\\Babel2'
APP_DATA_DIR = os.path.join(os.environ['LOCALAPPDATA'], 'Babel')
PROD_LOG_PATH = os.path.join(APP_DATA_DIR, 'log/babellog.out')
MY_DOCS = os.path.expanduser(os.sep.join(["~", "Documents"]))
USER_DATA = os.path.join(APP_DATA_DIR, 'user_data')


class SetupError(Exception):
    """Base class for exceptions in this module."""
    pass


class BusyManager:
    """cursor manager"""

    def __init__(self, widget):
        self.toplevel = widget.winfo_toplevel()
        self.widgets = {}

    def busy(self, widget=None):
        if widget is None:
            w = self.toplevel
        else:
            w = widget

        if str(w) not in self.widgets:
            try:
                # attach cursor to this widget
                cursor = w.cget("cursor")
                if cursor != "watch":
                    self.widgets[str(w)] = (w, cursor)
                    w.config(cursor="watch")
            except TclError:
                pass

        for w in w.children.values():
            self.busy(w)

    def notbusy(self):
        # restore cursors
        for w, cursor in self.widgets.values():
            try:
                w.config(cursor=cursor)
            except TclError:
                pass
        self.widgets = {}


def get_from_vault(application, user):
    """
    gets password for appliction/user from Windows Credential Locker
    args:
        application: string, name of applicaiton
        user: string, name of user
    returns:
        password: string
    """

    password = keyring.get_password(application, user)
    return password


def store_in_vault(application, user, password):
    """
    stores credentials in Windows Credential Locker
    args:
        applicaiton: string,  name of application
        user: string, name of user
        password: string
    """

    # check if credentials already stored and if so
    # delete and store updated ones
    try:
        if not get_from_vault(application, user):
            keyring.set_password(application, user, password)
        else:
            keyring.delete_password(application, user)
            keyring.set_password(application, user, password)
    except PasswordSetError as e:
        raise SetupError(e)
    except PasswordDeleteError as e:
        raise SetupError(e)


def prep_space(new_install=False):
    """
    Creates required by Babel folders
    args:
        new_install: Boolean, True - clean from scratch install,
                       False - only app not user data
    """

    # clean up previous installation files & folders
    try:
        shutil.rmtree(APP_DIR)
    except FileNotFoundError:
        pass
    except PermissionError as e:
        raise SetupError(e)

    try:
        if new_install:
            shutil.rmtree(APP_DATA_DIR)
    except FileNotFoundError:
        pass
    except PermissionError as e:
        raise SetupError(e)

    # recreate
    try:
        os.mkdir(APP_DIR)
    except PermissionError as e:
        raise SetupError(e)

    try:
        if new_install:
            os.mkdir(APP_DATA_DIR)
            os.mkdir(os.path.dirname(PROD_LOG_PATH))
    except PermissionError as e:
        raise SetupError(e)


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
            zip.extractall(APP_DIR)
            if status_var is not None:
                status_var.set('Unpacking complete.')

    except Exception as e:
        raise SetupError(e)


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

        img = Image.open('updater.png')
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

                user_data = shelve.open(USER_DATA)
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

            except SetupError as e:
                self.cur_manager.notbusy()
                messagebox.showerror(
                    'Setup error',
                    f'Unable to complete. Error: {e}')

    def find_zipfile(self):
        fh = filedialog.askopenfilename(initialdir=MY_DOCS)
        if fh:
            self.zipfile.set(fh)
            self.update_dir.set(os.path.dirname(self.zipfile.get()))
            self.status.set('zipfile selected...')


if __name__ == '__main__':

    # set the backend for credentials
    keyring.set_keyring(WinVaultKeyring())

    app = Installer()
    s = Style()
    s.theme_use('xpnative')
    s.configure('.', font=('device', 12))
    # app.iconbitmap('./icons/babel.ico')
    app.title('Babel Setup')
    app.mainloop()
