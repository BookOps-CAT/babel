# application launcher here

import logging
import logging.config
import logging.handlers
import keyring
from keyring.backends.Windows import WinVaultKeyring
from tkinter.ttk import Style
import shelve

from gui.main import Base
from logging_settings import DEV_LOGGING, LogglyAdapter, format_traceback
from paths import USER_DATA


def determine_version():
    about = {}
    with open('__version__.py') as f:
        exec(f.read(), about)
    return about['__version__']


if __name__ == '__main__':

    # babel directories will be installed via installer
    # here app will not be verifying if they exist

    # set up application logger
    logging.config.dictConfig(DEV_LOGGING)
    logger = logging.getLogger('babel_logger')
    error_logger = LogglyAdapter(logger, None)

    # set the backend for credentials
    keyring.set_keyring(WinVaultKeyring())

    # determine version, wonder if this will work after packaging
    # into frozen binaries?
    version = determine_version()

    # determine if babelstore is connected and if not
    # launch setup
    user_data = shelve.open(USER_DATA)
    if 'db_config' in user_data:
        datastore_linked = True
    else:
        datastore_linked = False
    user_data.close()

    if datastore_linked:
        app = Base()
        s = Style()
        s.theme_use('xpnative')
        s.configure('.', font=('device', 12))
        app.iconbitmap('./icons/babel.ico')
        app.title('Babel v.{}'.format(version))
        app.mainloop()
    else:
        print('Babel datastore setup should launch here.')
