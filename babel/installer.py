import ast
import json
import logging
import os
import time
import shelve
import shutil
import sys
from tkinter import *
from tkinter import messagebox, filedialog
from tkinter.ttk import *

from PIL import Image, ImageTk

try:
    from errors import BabelError
    from gui.utils import BusyManager
    from credentials import get_from_vault, decrypt_file_data, store_in_vault
    from paths import USER_DATA, APP_DATA_DIR, PROD_LOG_PATH
except ImportError:
    # needed for pytest
    from .errors import BabelError
    from .gui.utils import BusyManager
    from .credentials import get_from_vault
    from .paths import USER_DATA, APP_DATA_DIR, PROD_LOG_PATH


ilogger = logging.getLogger()
ilogger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
ilogger.addHandler(handler)


def has_creds_config_in_user_data(user_data):
    if "babel" in user_data and user_data["babel"]:
        return True
    else:
        return False


def has_creds_in_vault(app, user):
    if get_from_vault(app, user) is not None:
        return True
    else:
        return False


def has_user_data_file():
    return os.path.isfile(f"{USER_DATA}.dat")


def is_configured():
    """
    Determines if all requried components and credentials
    are present
    """
    has_data_file = has_data_file()
    ilogger.debug(f"Init: user data file located: {has_data_file}")

    if has_data_file:
        user_data = shelve.open(USER_DATA)
        has_db_config = has_creds_config_in_user_data(user_data)
        ilogger.debug(f"Init: found database config data: {has_db_config}")
        try:
            has_creds = has_creds_in_vault("babelprod", user_data["babelprod"])
            ilogger.debug(f"Init: has credential stored in vault: {has_creds}")
        except KeyError:
            ilogger.error(f"Init: Malformed db_config in user_data.")

        user_data.close()

    if has_data_file and has_db_config and has_creds:
        ilogger.debug("Init: app is configured.")
        return True
    else:
        ilogger.debug("Init: app not configured!")
        return False


class Installer(Tk):
    def __init__(self, *args, **kwargs):
        ilogger.debug("Init: launching configuration window.")
        Tk.__init__(self, *args, **kwargs)

        frm = Frame(self)
        # container.columnconfigure(1, minsize=150)
        frm.grid(padx=20, pady=20)
        # bind shared data between windows
        self.key = StringVar()
        self.status = StringVar()
        self.status.set("Please provide decryption key")

        self.cur_manager = BusyManager(self)

        infoFrm = Frame(frm)
        infoFrm.grid(row=0, column=0, sticky="snew", padx=10, pady=10)

        img = Image.open("./icons/PadLock-icon.png")
        logo = ImageTk.PhotoImage(img)
        logoImg = Label(infoFrm, image=logo)
        logoImg.image = logo
        logoImg.grid(row=0, column=0, sticky="snew", padx=10, pady=10)

        actionFrm = LabelFrame(frm, text="Babel password")
        actionFrm.grid(row=0, column=1, sticky="snew", padx=10, pady=10)
        # actionFrm.columnconfigure(1, minsize=250)
        actionFrm.rowconfigure(1, minsize=10)
        actionFrm.rowconfigure(3, minsize=10)

        keyEnt = Entry(actionFrm, textvariable=self.key, show="*")
        keyEnt.grid(row=0, column=0, columnspan=2, sticky="snew", padx=5, pady=3)

        self.statusLbl = Label(actionFrm, textvariable=self.status, anchor=CENTER)
        self.statusLbl.grid(
            row=2, column=0, columnspan=2, sticky="snew", padx=10, pady=10
        )

        configBtn = Button(actionFrm, text="unlock", command=self.launch_config)
        configBtn.grid(row=4, column=0, sticky="snew", padx=10, pady=10)

        cancelBtn = Button(actionFrm, text="cancel", command=self.destroy)
        cancelBtn.grid(row=4, column=1, sticky="snw", padx=10, pady=10)

    def launch_config(self):
        # prep data directory
        try:
            self.create_data_dir()
            space_preped = True
        except PermissionError:
            self.status.set("Permission error encoutered.")
            space_preped = False

        if space_preped:
            # credentials
            ilogger.debug("Init: AppData/Local/Babel directory created.")
            if os.path.isfile("creds.bin"):
                ilogger.debug("Init: creds.bin file found.")
                creds = self.decrypt()
            else:
                creds = None
                ilogger.debug("Init: creds.bin not found.")
                self.status.set("credentials file not found.")

        if creds:
            self.store_creds(creds)

    def decrypt(self):
        try:
            self.status.set("Decrypting...")
            self.statusLbl.update()
            decrypted = decrypt_file_data(
                self.key.get().strip().encode("utf8"), "creds.bin"
            )
            ilogger.debug("Init: creds.bin decrypted.")
            creds = json.loads(decrypted)
            return creds
        except BabelError as exc:
            ilogger.error(f"Init: ValueError: {exc}")
            self.status.set(f"Value error. Try again.")
            return None

    def create_data_dir(self):
        if not has_user_data_file():
            # clean up local dir
            try:
                shutil.rmtree(APP_DATA_DIR)
            except FileNotFoundError:
                ilogger.debug("Init: No Babel direcrtoy in AppData/Local.")
            except PermissionError as exc:
                ilogger.error(
                    f"Init: Unable to delete current Babel directory in AppData/Local. Error: {exc}"
                )
                raise

            # recreate
            try:
                os.mkdir(APP_DATA_DIR)
                os.mkdir(os.path.dirname(PROD_LOG_PATH))
            except PermissionError as exc:
                ilogger.error(
                    f"Init: Unable to create Babel directory in AppData/Local. Error: {exc}"
                )
                raise

    def store_creds(self, creds):
        # create user_data
        user_data = shelve.open(USER_DATA)

        user_data["db_config"] = dict(
            db_name=creds["db_name"],
            host=creds["host"],
            user=creds["user"],
            port=creds["port"],
        )
        user_data.close()
        ilogger.debug("Init: MySql data stored in the user_data file.")

        try:
            store_in_vault(creds["db_name"], creds["user"], creds["passw"])
            ilogger.debug("Init: MySql password stored in Windows Credential Manager.")
            self.status.set("Success! Closing. Please restart Babel.")
            self.statusLbl.update()
            time.sleep(3)
            self.destroy()
        except BabelError as exc:
            ilogger.error(
                f"Init: Unable to store MySql cred in Windows Credential Manger. Error: {exc}"
            )
            self.status.set("Unable to store DB credentials.")
