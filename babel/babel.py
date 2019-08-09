# application launcher here

import logging
import logging.config
import os
from tkinter.ttk import Style
import shelve

import logging.handlers
import keyring
from keyring.backends.Windows import WinVaultKeyring


from gui.main import Base, determine_version
from logging_settings import DEV_LOGGING, LogglyAdapter, format_traceback
from paths import USER_DATA


if __name__ == '__main__':

    # babel directories will be installed via installer
    # here app will not be verifying if they exist

    # set up application logger
    logging.config.dictConfig(DEV_LOGGING)
    logger = logging.getLogger('babel_logger')
    error_logger = LogglyAdapter(logger, None)

    # set the backend for credentials
    keyring.set_keyring(WinVaultKeyring())

    user_data = shelve.open(USER_DATA)
    # determine if babelstore is connected and if not
    # launch setup
    if 'db_config' in user_data:
        datastore_linked = True
    else:
        datastore_linked = False
    user_data.close()

    if datastore_linked:
        local_version = determine_version(os.getcwd())
        app = Base()
        s = Style()
        s.theme_use('xpnative')
        s.configure('.', font=('device', 12))
        app.iconbitmap('./icons/babel2.ico')
        app.title('Babel v.{}'.format(local_version))
        app.mainloop()
    else:
        # widget displaying error msg?
        pass
