import logging
import os
import shelve
from tkinter import *
from tkinter import messagebox, filedialog
from tkinter.ttk import *

from PIL import Image, ImageTk

try:
    from gui.utils import BusyManager
    from credentials import get_from_vault
    from logging_settings import LogglyAdapter
    from paths import USER_DATA
except ImportError:
    # needed for pytest
    from .gui.utils import BusyManager
    from .credentials import get_from_vault
    from .logging_settings import LogglyAdapter
    from .paths import USER_DATA


mlogger = LogglyAdapter(logging.getLogger("babel"), None)


def has_db_config_in_user_data(user_data):
    if "db_config" in user_data:
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
    user_data = shelve.open(USER_DATA)

    has_data_file = has_user_data_file()
    mlogger.debug(f"Init: found data file: {has_data_file}")
    has_db_config = has_db_config_in_user_data(user_data)
    mlogger.debug(f"Init: found database config data: {has_db_config}")
    has_creds = has_creds_in_vault(
        user_data["db_config"]["db_name"], user_data["db_config"]["user"]
    )
    mlogger.debug(f"Init: has credential stored in vault: {has_creds}")
    user_data.close()

    if has_data_file and has_db_config and has_creds:
        mlogger.debug("Init: app is configured.")
        return True
    else:
        mlogger.debug("Init: app not configured!")
        return False


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
        infoFrm.grid(row=0, column=0, sticky="snew", padx=10, pady=10)

        img = Image.open("updater.png")
        logo = ImageTk.PhotoImage(img)
        logoImg = Label(infoFrm, image=logo)
        logoImg.image = logo
        logoImg.grid(row=0, column=0, sticky="snew", padx=10, pady=10)

        Label(infoFrm, text="Babel 2 Installer", anchor=CENTER).grid(
            row=1, column=0, sticky="snew", padx=10, pady=10
        )

        self.statusLbl = Label(infoFrm, textvariable=self.status, anchor=CENTER)
        self.statusLbl.grid(row=2, column=0, sticky="snew", padx=10, pady=10)

        dbFrm = LabelFrame(frm, text="Babel database configuration:")
        dbFrm.grid(row=0, column=1, sticky="snew", padx=10, pady=10)
        dbFrm.columnconfigure(1, minsize=250)

        Label(dbFrm, text="host:").grid(row=0, column=0, sticky="snw", padx=5, pady=3)
        hostEnt = Entry(dbFrm, textvariable=self.db_host)
        hostEnt.grid(row=0, column=1, sticky="snew", padx=5, pady=3)

        Label(dbFrm, text="database:").grid(
            row=1, column=0, sticky="snw", padx=5, pady=3
        )
        nameEnt = Entry(dbFrm, textvariable=self.db_name)
        nameEnt.grid(row=1, column=1, sticky="snew", padx=5, pady=3)

        Label(dbFrm, text="port:").grid(row=2, column=0, sticky="snw", padx=5, pady=3)
        portEnt = Entry(dbFrm, textvariable=self.db_port)
        portEnt.grid(row=2, column=1, sticky="snew", padx=5, pady=3)

        Label(dbFrm, text="user:").grid(row=3, column=0, sticky="snw", padx=5, pady=3)
        userEnt = Entry(dbFrm, textvariable=self.db_user)
        userEnt.grid(row=3, column=1, sticky="snew", padx=5, pady=3)

        Label(dbFrm, text="password:").grid(
            row=4, column=0, sticky="snw", padx=5, pady=3
        )
        passwEnt = Entry(dbFrm, textvariable=self.db_passw)
        passwEnt.grid(row=4, column=1, sticky="snew", padx=5, pady=3)

        btnFrm = Frame(frm)
        btnFrm.grid(row=1, column=1, sticky="snew", padx=10, pady=10)

        browseBtn = Button(btnFrm, text="browse", command=self.find_zipfile)
        browseBtn.grid(row=0, column=0, sticky="snew", padx=10, pady=10)

        installBtn = Button(btnFrm, text="install", command=self.launch_install)
        installBtn.grid(row=0, column=1, sticky="snew", padx=10, pady=10)

        cancelBtn = Button(btnFrm, text="cancel", command=self.destroy)
        cancelBtn.grid(row=0, column=2, sticky="snw", padx=10, pady=10)

    def launch_install(self):
        missing = []
        if not self.db_host.get():
            missing.append("database host")
        if not self.db_port.get():
            missing.append("database port")
        if not self.db_name.get():
            missing.append("database name")
        if not self.db_user.get():
            missing.append("user")
        if not self.db_passw.get():
            missing.append("password")

        if missing:
            missing_str = "\n  -".join(missing)
            messagebox.showwarning(
                "Input error",
                "Missing database configuration parameters:" f"\n  -{missing_str}",
            )
        else:
            try:
                self.cur_manager.busy()
                prep_space(new_install=True)
                unpack(self.zipfile.get(), self.status)

                user_data = shelve.open(USER_DATA)
                user_data["update_dir"] = os.path.join(self.update_dir.get(), "app")
                db_config = dict(
                    db_name=self.db_name.get().strip(),
                    host=self.db_host.get().strip(),
                    port=self.db_port.get().strip(),
                    user=self.db_user.get().strip(),
                )
                user_data["db_config"] = db_config
                user_data.close()

                self.status.set("Saving creds.")

                store_in_vault(
                    db_config["db_name"], db_config["user"], self.db_passw.get().strip()
                )

                self.cur_manager.notbusy()
                self.status.set("Setup complete.")
                messagebox.showinfo("Babel setup", "Installation successful.")

            except SetupError as e:
                self.cur_manager.notbusy()
                messagebox.showerror("Setup error", f"Unable to complete. Error: {e}")

            except Exception as e:
                self.cur_manager.notbusy()
                messagebox.showerror("Setup error", f"Unable to complete. Error: {e}")
