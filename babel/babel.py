# application launcher here

import logging
import logging.config
import logging.handlers
# import sys
from tkinter.ttk import Style

from gui.main import Base
from logging_settings import DEV_LOGGING, LogglyAdapter, format_traceback
# from paths import APP_DATA_DIR


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

    # determine version
    version = determine_version()

    # launch application
    app = Base()
    s = Style()
    s.theme_use('xpnative')
    app.iconbitmap('./icons/babel.ico')
    app.title('Babel v.{}'.format(version))

    print(s.theme_names())
    # s.configure(
    #     '.',
    #     background='white')
    # s.configure('TFrame', background='white')
    # s.map('Regular.TButton', background=[('active', 'white')])
    # s.configure('Flat.TEntry', borderwidth=0)
    # s.configure('Bold.TLabel', font=('Helvetica', 12, 'bold'))
    # s.configure('Small.TLabel', font=('Helvetica', 8))
    # s.configure('Medium.Treeview', font=('Helvetica', 9))
    app.mainloop()
