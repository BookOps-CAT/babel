import logging
import shelve
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox


from credentials import store_in_vault
from data.datastore import DB_DIALECT, DB_DRIVER, DB_CHARSET
from errors import BabelError
from gui.fonts import RFONT
from gui.utils import ToolTip, disable_widgets, open_url
from logging_settings import LogglyAdapter
from paths import USER_DATA


mlogger = LogglyAdapter(logging.getLogger("babel"), None)


class SettingsView(Frame):
    """
    Datastore database settings view
    """

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        Frame.__init__(self, parent)
        self.controller = controller
        self.app_data = app_data
        self.activeW = app_data["activeW"]
        self.activeW.trace("w", self.observer)

        # local variables
        self.dialect = StringVar()
        self.driver = StringVar()
        self.db_host = StringVar()
        self.db_port = StringVar()
        self.db_name = StringVar()
        self.db_user = StringVar()
        self.db_passw = StringVar()
        self.chr_enc = StringVar()

        # icons
        # getImg = self.app_data['img']['view']
        saveImg = self.app_data["img"]["save"]
        editImg = self.app_data["img"]["edit"]
        helpImg = self.app_data["img"]["help"]

        # layout
        # main frame
        self.mainFrm = Frame(self)
        self.mainFrm.grid(row=0, column=0, sticky="snew", padx=20, pady=20)

        # left nav buttons
        # self.credsBtn = Button(
        #     self.mainFrm,
        #     image=getImg,
        #     command=self.get_access)
        # self.credsBtn.grid(
        #     row=0, column=0, sticky='sw', padx=10, pady=5)
        # self.createToolTip(self.credsBtn, 'auto credentials')

        self.editDbBtn = Button(
            self.mainFrm, image=editImg, command=self.edit_db_access
        )
        self.editDbBtn.grid(row=1, column=0, sticky="sw", padx=10, pady=5)
        self.createToolTip(self.editDbBtn, "edit database accesss")

        self.saveDbBtn = Button(
            self.mainFrm, image=saveImg, command=self.save_db_access
        )
        self.saveDbBtn.grid(row=2, column=0, sticky="sw", padx=10, pady=5)
        self.createToolTip(self.saveDbBtn, "save changes")

        self.helpBtn = Button(self.mainFrm, image=helpImg, command=self.help)
        self.helpBtn.grid(row=3, column=0, sticky="sw", padx=10, pady=5)
        self.createToolTip(self.helpBtn, "show help")

        # database access details
        self.detFrm = LabelFrame(self, text="Database details")
        self.detFrm.grid(row=0, column=1, sticky="snew", padx=20, pady=20)
        self.detFrm.columnconfigure(1, minsize=400)

        Label(self.detFrm, text="dialect:").grid(
            row=0, column=0, sticky="snw", padx=10, pady=4
        )
        self.dialectCbx = Combobox(self.detFrm, font=RFONT, textvariable=self.dialect)
        self.dialectCbx.grid(row=0, column=1, sticky="snew", padx=10, pady=4)

        Label(self.detFrm, text="driver:").grid(
            row=1, column=0, sticky="snw", padx=10, pady=4
        )
        self.driverCbx = Combobox(self.detFrm, font=RFONT, textvariable=self.driver)
        self.driverCbx.grid(row=1, column=1, sticky="snew", padx=10, pady=4)

        Label(self.detFrm, text="host:").grid(
            row=2, column=0, sticky="snw", padx=10, pady=4
        )
        self.db_hostEnt = Entry(self.detFrm, font=RFONT, textvariable=self.db_host)
        self.db_hostEnt.grid(row=2, column=1, sticky="snew", padx=10, pady=4)

        Label(self.detFrm, text="port:").grid(
            row=3, column=0, sticky="snw", padx=10, pady=4
        )
        self.db_portEnt = Entry(self.detFrm, font=RFONT, textvariable=self.db_port)
        self.db_portEnt.grid(row=3, column=1, sticky="snew", padx=10, pady=4)

        Label(self.detFrm, text="db name:").grid(
            row=4, column=0, sticky="snw", padx=10, pady=4
        )
        self.dbnameEnt = Entry(self.detFrm, font=RFONT, textvariable=self.db_name)
        self.dbnameEnt.grid(row=4, column=1, sticky="snew", padx=10, pady=4)

        Label(self.detFrm, text="user:").grid(
            row=5, column=0, sticky="snw", padx=10, pady=4
        )
        self.db_userEnt = Entry(self.detFrm, font=RFONT, textvariable=self.db_user)
        self.db_userEnt.grid(row=5, column=1, sticky="snew", padx=10, pady=4)

        Label(self.detFrm, text="password:").grid(
            row=6, column=0, sticky="snw", padx=10, pady=4
        )
        self.db_passwEnt = Entry(
            self.detFrm, font=RFONT, show="*", textvariable=self.db_passw
        )
        self.db_passwEnt.grid(row=6, column=1, sticky="snew", padx=10, pady=4)

        Label(self.detFrm, text="encoding:").grid(
            row=7, column=0, sticky="snw", padx=10, pady=4
        )
        self.chrencCbx = Combobox(self.detFrm, font=RFONT, textvariable=self.chr_enc)
        self.chrencCbx.grid(row=7, column=1, sticky="snew", padx=10, pady=4)

    def edit_db_access(self):
        self.db_hostEnt["state"] = "!disable"
        self.db_portEnt["state"] = "!disable"
        self.dbnameEnt["state"] = "!disable"
        self.db_userEnt["state"] = "!disable"
        self.db_passwEnt["state"] = "!disable"
        self.db_passw.set("")

    def save_db_access(self):
        missing = []
        if not self.db_name.get().strip():
            missing.append("db name")
        if not self.db_user.get().strip():
            missing.append("user")
        if not self.db_passw.get().strip():
            missing.append("password")
        if not self.db_host.get().strip():
            missing.append("host")
        if not self.db_port.get().strip():
            missing.append("port")

        if not missing:
            user_data = shelve.open(USER_DATA)
            db_config = dict(
                DB_NAME=self.db_name.get().strip(),
                DB_USER=self.db_user.get().strip(),
                DB_HOST=self.db_host.get().strip(),
                DB_PORT=self.db_port.get().strip(),
            )
            user_data["db_config"] = db_config
            user_data.close()

            # save password
            try:
                store_in_vault(
                    "babel_db",
                    self.db_user.get().strip(),
                    self.db_passw.get().strip(),
                )
            except BabelError as e:
                mlogger.error(f"DB store_in_vault error. Error: {e}")
            disable_widgets(self.detFrm.winfo_children())
        else:
            messagebox.showwarning(
                "Input Error",
                "Missing element(s): \n  -{}".format("\n  -".join(missing)),
            )

    def help(self):
        pass

    def observer(self, *args):
        if self.activeW.get() == "SettingsView":
            # pull & display data
            self.dialect.set(DB_DIALECT)
            self.driver.set(DB_DRIVER)
            self.chr_enc.set(DB_CHARSET)

            user_data = shelve.open(USER_DATA)
            db_config = user_data["db_config"]
            self.db_name.set(db_config["DB_NAME"])
            self.db_user.set(db_config["DB_USER"])
            self.db_host.set(db_config["DB_HOST"])
            self.db_port.set(db_config["DB_PORT"])
            user_data.close()

            self.db_passw.set("dummy passw")

            disable_widgets(self.detFrm.winfo_children())

    def createToolTip(self, widget, text):
        toolTip = ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
