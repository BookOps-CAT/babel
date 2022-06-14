import logging
import traceback

try:
    from paths import DEV_LOG_PATH, PROD_LOG_PATH
except ImportError:
    from babel.paths import DEV_LOG_PATH, PROD_LOG_PATH


PROD_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "brief": {
            "format": "%(name)s-%(asctime)s-%(filename)s-%(lineno)s-%(levelname)s-%(levelno)s-%(message)s"
        },
        "json": {
            "format": '{"app":"%(name)s", "asciTime":"%(asctime)s", "fileName":"%(filename)s", "lineNo":"%(lineno)d", "levelName":"%(levelname)s", "message":"%(message)s"}'
        },
    },
    "handlers": {
        "loggly": {
            "level": "ERROR",
            "class": "loggly.handlers.HTTPSHandler",
            "formatter": "json",
            "url": "https://logs-01.loggly.com/inputs/[token]/tag/python",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": PROD_LOG_PATH,
            "formatter": "brief",
            "maxBytes": 1024 * 1024,
            "backupCount": 5,
        },
    },
    "loggers": {
        "babel": {"handlers": ["loggly", "file"], "level": "DEBUG", "propagate": True}
    },
}


DEV_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "brief": {
            "format": "%(name)s-%(asctime)s-%(filename)s-%(lineno)s-%(levelname)s-%(message)s"
        },
        "json": {
            "format": '{"app":"%(name)s", "asciTime":"%(asctime)s", "fileName":"%(filename)s", "lineNo":"%(lineno)d", "levelName":"%(levelname)s", "message":"%(message)s"}'
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "brief",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": DEV_LOG_PATH,
            "formatter": "brief",
            "maxBytes": 1024 * 1024,
            "backupCount": 5,
        },
    },
    "loggers": {
        "babel": {"handlers": ["console", "file"], "level": "DEBUG", "propagate": True}
    },
}


class LogglyAdapter(logging.LoggerAdapter):
    """
    Adapter for Loggly service that escapes JSON special characters in msg
    """

    def process(self, msg, kwargs):
        try:
            format_msg = "%s" % (
                msg.replace("\\", "/")
                .replace('"', "")
                .replace("'", "")
                .replace("\n", "\\n")
                .replace("\t", "\\t")
            )
        except AttributeError:
            format_msg = msg

        return format_msg, kwargs


def format_traceback(exc, exc_traceback=None):
    """
    Formats logging tracebacks into a string accepted by Loggly service (JSON).
    args:
        exc: type, exceptions
        exc_traceback: type, traceback obtained from sys.exc_info()
    returns:
        traceback: string of joined traceback lines

    usage:
        try:
            int('a')
        except ValueError as exc:
            _, _, exc_traceback = sys.exc_info()
            tb = format_traceback(exc, exc_traceback)
            logger.error('Unhandled error. {}'.format(tb))
    """

    if exc_traceback is None:
        exc_traceback = exc.__traceback__

    return "".join(traceback.format_exception(exc.__class__, exc, exc_traceback))
