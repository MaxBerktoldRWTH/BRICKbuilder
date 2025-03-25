import enum
import logging


__all__ = ['Logger', 'LogLevel']


class LogLevel(int, enum.Enum):

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class Logger(logging.Logger):

    DEFAULT: int = logging.WARNING

    def __init__(self, obj: object, level: int = None):

        super().__init__(name=str(obj))

        formatter = CustomFormatter()

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        self.addHandler(handler)

        if level is None:
            level = self.DEFAULT

        self.setLevel(level)

    @staticmethod
    def setGlobalLevel(level: int):

        loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
        for logger in loggers:
            logger.setLevel(level)

    @staticmethod
    def setDefaultLevel(level: int | str):
        Logger.DEFAULT = level


class CustomFormatter(logging.Formatter):

    experiment = '\033[20m'
    light_grey = '\033[97m'
    green = '\033[32m'
    white = '\033[37m'
    grey = '\033[37m'
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s | %(name)s | %(message)s "

    #%(levelname)-8s

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: experiment + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):

        log_fmt = self.FORMATS[record.levelno]
        formatter = logging.Formatter(
            log_fmt,
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        return formatter.format(record)


if __name__ == '__main__':

    logger = Logger('some', level=logging.DEBUG)

    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warning message")
    logger.error("error message")
    logger.critical("critical message")

