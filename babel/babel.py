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


# set up application logger


# set the backend for credentials
keyring.set_keyring(WinVaultKeyring())

# determine if babelstore is connected and if not
# launch setup
if is_configured() is True:
    app_ready = True
else:
    app_ready = False

# app_ready = False

if app_ready:
    from gui.main import Base, determine_version

    logging.config.dictConfig(DEV_LOGGING)
    logger = logging.getLogger("babel")

    local_version = determine_version(os.getcwd())
    app = Base()
    s = Style()
    s.theme_use("xpnative")
    s.configure(".", font=("device", 12))
    app.iconbitmap("./icons/babel2.ico")
    app.title("Babel v.{}".format(local_version))
    app.mainloop()
else:
    app = Installer()
    s = Style()
    s.theme_use("xpnative")
    s.configure(".", font=("device", 12))
    app.iconbitmap("./icons/babel2.ico")
    app.title("Babel Setup")
    app.mainloop()
