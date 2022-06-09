import logging
import shelve
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox


from credentials import get_from_vault, store_in_vault
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
        self.db_dialect = StringVar()
        self.db_driver = StringVar()
        self.db_host = StringVar()
        self.db_port = StringVar()
        self.db_name = StringVar()
        self.db_user = StringVar()
        self.db_passw = StringVar()
        self.db_chr_enc = StringVar()
        self.plat_oauth = StringVar()
        self.plat_client_id = StringVar()
        self.plat_secret = StringVar()
        self.solr_endpoint = StringVar()
        self.solr_secret = StringVar()

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

        # Database buttons
        self.editBtn = Button(self.mainFrm, image=editImg, command=self.edit_access)
        self.editBtn.grid(row=1, column=0, sticky="sw", padx=10, pady=5)
        self.createToolTip(self.editBtn, "edit credentials")

        self.saveBtn = Button(self.mainFrm, image=saveImg, command=self.save_access)
        self.saveBtn.grid(row=2, column=0, sticky="sw", padx=10, pady=5)
        self.createToolTip(self.saveBtn, "save changes")

        self.helpBtn = Button(self.mainFrm, image=helpImg, command=self.help)
        self.helpBtn.grid(row=10, column=0, sticky="sw", padx=10, pady=5)
        self.createToolTip(self.helpBtn, "show help")

        # database access details
        self.dbFrm = LabelFrame(self, text="Database details")
        self.dbFrm.columnconfigure(0, minsize=120)
        self.dbFrm.columnconfigure(1, minsize=400)
        self.dbFrm.grid(row=0, column=1, sticky="snew", padx=20, pady=10)

        Label(self.dbFrm, text="dialect:").grid(
            row=0, column=0, sticky="snw", padx=10, pady=4
        )
        self.db_dialectCbx = Combobox(
            self.dbFrm, font=RFONT, textvariable=self.db_dialect
        )
        self.db_dialectCbx.grid(row=0, column=1, sticky="snew", padx=10, pady=4)

        Label(self.dbFrm, text="driver:").grid(
            row=1, column=0, sticky="snw", padx=10, pady=4
        )
        self.db_driverCbx = Combobox(
            self.dbFrm, font=RFONT, textvariable=self.db_driver
        )
        self.db_driverCbx.grid(row=1, column=1, sticky="snew", padx=10, pady=4)

        Label(self.dbFrm, text="host:").grid(
            row=2, column=0, sticky="snw", padx=10, pady=4
        )
        self.db_hostEnt = Entry(self.dbFrm, font=RFONT, textvariable=self.db_host)
        self.db_hostEnt.grid(row=2, column=1, sticky="snew", padx=10, pady=4)

        Label(self.dbFrm, text="port:").grid(
            row=3, column=0, sticky="snw", padx=10, pady=4
        )
        self.db_portEnt = Entry(self.dbFrm, font=RFONT, textvariable=self.db_port)
        self.db_portEnt.grid(row=3, column=1, sticky="snew", padx=10, pady=4)

        Label(self.dbFrm, text="db name:").grid(
            row=4, column=0, sticky="snw", padx=10, pady=4
        )
        self.dbnameEnt = Entry(self.dbFrm, font=RFONT, textvariable=self.db_name)
        self.dbnameEnt.grid(row=4, column=1, sticky="snew", padx=10, pady=4)

        Label(self.dbFrm, text="user:").grid(
            row=5, column=0, sticky="snw", padx=10, pady=4
        )
        self.db_userEnt = Entry(self.dbFrm, font=RFONT, textvariable=self.db_user)
        self.db_userEnt.grid(row=5, column=1, sticky="snew", padx=10, pady=4)

        Label(self.dbFrm, text="password:").grid(
            row=6, column=0, sticky="snw", padx=10, pady=4
        )
        self.db_passwEnt = Entry(
            self.dbFrm, font=RFONT, show="*", textvariable=self.db_passw
        )
        self.db_passwEnt.grid(row=6, column=1, sticky="snew", padx=10, pady=4)

        Label(self.dbFrm, text="encoding:").grid(
            row=7, column=0, sticky="snw", padx=10, pady=4
        )
        self.chrencCbx = Combobox(self.dbFrm, font=RFONT, textvariable=self.db_chr_enc)
        self.chrencCbx.grid(row=7, column=1, sticky="snew", padx=10, pady=4)

        # NYPL Platform details
        self.platFrm = LabelFrame(self, text="NYPL Platform")
        self.platFrm.columnconfigure(0, minsize=120)
        self.platFrm.columnconfigure(1, minsize=400)
        self.platFrm.grid(row=1, column=1, sticky="snew", padx=20, pady=10)

        Label(self.platFrm, text="oauth server:").grid(
            row=0, column=0, sticky="snw", padx=10, pady=4
        )
        self.plat_oauthEnt = Entry(
            self.platFrm, font=RFONT, textvariable=self.plat_oauth
        )
        self.plat_oauthEnt.grid(row=0, column=1, sticky="snew", padx=10, pady=4)

        Label(self.platFrm, text="client id:").grid(
            row=1, column=0, sticky="snw", padx=10, pady=4
        )
        self.plat_clientEnt = Entry(
            self.platFrm, font=RFONT, textvariable=self.plat_client_id
        )
        self.plat_clientEnt.grid(row=1, column=1, sticky="snew", padx=10, pady=4)

        Label(self.platFrm, text="secret:").grid(
            row=2, column=0, sticky="snw", padx=10, pady=4
        )
        self.plat_secretEnt = Entry(
            self.platFrm, font=RFONT, show="*", textvariable=self.plat_secret
        )
        self.plat_secretEnt.grid(row=2, column=1, sticky="snew", padx=10, pady=4)

        # BPL Solr details
        self.solrFrm = LabelFrame(self, text="BPL Solr")
        self.solrFrm.columnconfigure(0, minsize=120)
        self.solrFrm.columnconfigure(1, minsize=400)
        self.solrFrm.grid(row=2, column=1, sticky="snew", padx=20, pady=10)

        Label(self.solrFrm, text="endpoint:").grid(
            row=0, column=0, sticky="snw", padx=10, pady=4
        )
        self.solr_endEnt = Entry(
            self.solrFrm, font=RFONT, textvariable=self.solr_endpoint
        )
        self.solr_endEnt.grid(row=0, column=1, sticky="snew", padx=10, pady=4)

        Label(self.solrFrm, text="secret:").grid(
            row=1, column=0, sticky="snw", padx=10, pady=4
        )
        self.solr_secretEnt = Entry(
            self.solrFrm, font=RFONT, show="*", textvariable=self.solr_secret
        )
        self.solr_secretEnt.grid(row=1, column=1, sticky="snew", padx=10, pady=4)

    def edit_access(self):
        self.db_hostEnt["state"] = "!disable"
        self.db_portEnt["state"] = "!disable"
        self.dbnameEnt["state"] = "!disable"
        self.db_userEnt["state"] = "!disable"
        self.db_passwEnt["state"] = "!disable"

        self.plat_oauthEnt["state"] = "!disable"
        self.plat_clientEnt["state"] = "!disable"
        self.plat_secretEnt["state"] = "!disable"

        self.solr_endEnt["state"] = "!disable"
        self.solr_secretEnt["state"] = "!disable"

    def save_access(self):
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

            plat_config = dict(
                PLATFORM_OAUTH_SERVER=self.plat_oauth.get().strip(),
                PLATFORM_CLIENT_ID=self.plat_client_id.get().strip(),
            )

            user_data["nyp_platform"] = plat_config

            solr_config = dict(SOLR_ENDPOINT=self.solr_endpoint.get().strip())
            user_data["bpl_solr"] = solr_config

            user_data.close()

            # save password
            try:
                store_in_vault(
                    "babel_db",
                    self.db_user.get().strip(),
                    self.db_passw.get().strip(),
                )
                store_in_vault(
                    "babel_platform",
                    self.plat_client_id.get().strip(),
                    self.plat_secret.get().strip(),
                )
                store_in_vault("babel_solr", "babel", self.solr_secret.get().strip())
            except BabelError as e:
                mlogger.error(f"DB store_in_vault error. Error: {e}")
            disable_widgets(self.dbFrm.winfo_children())
            disable_widgets(self.platFrm.winfo_children())
            disable_widgets(self.solrFrm.winfo_children())
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
            self.db_dialect.set(DB_DIALECT)
            self.db_driver.set(DB_DRIVER)
            self.db_chr_enc.set(DB_CHARSET)

            user_data = shelve.open(USER_DATA)

            db_config = user_data["db_config"]
            self.db_name.set(db_config["DB_NAME"])
            self.db_user.set(db_config["DB_USER"])
            self.db_host.set(db_config["DB_HOST"])
            self.db_port.set(db_config["DB_PORT"])
            self.db_passw.set(get_from_vault("babel_db", db_config["DB_USER"]))

            plat_config = user_data["nyp_platform"]
            self.plat_oauth.set(plat_config["PLATFORM_OAUTH_SERVER"])
            self.plat_client_id.set(plat_config["PLATFORM_CLIENT_ID"])
            self.plat_secret.set(
                get_from_vault("babel_platform", plat_config["PLATFORM_CLIENT_ID"])
            )

            solr_config = user_data["bpl_solr"]
            self.solr_endpoint.set(solr_config["SOLR_ENDPOINT"])
            self.solr_secret.set(get_from_vault("babel_solr", "babel"))

            user_data.close()

            disable_widgets(self.dbFrm.winfo_children())
            disable_widgets(self.platFrm.winfo_children())
            disable_widgets(self.solrFrm.winfo_children())

    def createToolTip(self, widget, text):
        toolTip = ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
