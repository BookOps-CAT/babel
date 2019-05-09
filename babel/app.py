# application launcher here

import logging
import logging.config
import logging.handlers
import sys

from logging_settings import DEV_LOGGING, LogglyAdapter, format_traceback
from paths import APP_DATA_DIR


if __name__ == '__main__':

    # babel directories will be installed via installer
    # here app will not be verifying if they exist

    # set up application logger
    logging.config.dictConfig(DEV_LOGGING)
    logger = logging.getLogger('babel_logger')
    error_logger = LogglyAdapter(logger, None)

