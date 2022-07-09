# application launcher here

import logging
import logging.config
import os
from tkinter.ttk import Style

import loggly.handlers
import keyring
from keyring.backends.Windows import WinVaultKeyring


# from credentials import get_from_vault

from installer import is_configured, Installer
from logging_settings import DEV_LOGGING, PROD_LOGGING

VERSION = "4.0.0"

# set the backend for credentials
keyring.set_keyring(WinVaultKeyring())

# check if app is ready/configured and if not launch
# the installer
if is_configured():
    from gui.main import Base

    logging.config.dictConfig(DEV_LOGGING)
    logger = logging.getLogger("babel")

    app = Base()
    s = Style()
    s.theme_use("xpnative")
    s.configure(".", font=("device", 12))
    app.iconbitmap("./icons/babel2.ico")
    app.title(f"Babel v.{VERSION}")
    app.mainloop()
else:
    app = Installer()
    s = Style()
    s.theme_use("xpnative")
    s.configure(".", font=("device", 12))
    app.iconbitmap("./icons/babel2.ico")
    app.title("Babel Setup")
    app.mainloop()
