import sty
from inspect import stack
import pathlib


class Logger:
    @staticmethod
    def log(message):
        callerStackFrame = stack()[2]
        callerFile = callerStackFrame.filename
        callerFileName = f"[{pathlib.Path(callerFile).name}]"
        print(f"{callerFileName:<20} {message}")

    @staticmethod
    def logDebug(message):
        Logger.log(sty.fg.grey + message + sty.rs.all)

    @staticmethod
    def logInfo(message):
        Logger.log(sty.fg.li_cyan + message + sty.rs.all)

    @staticmethod
    def logWarning(message):
        Logger.log(sty.fg.yellow + message + sty.rs.all)

    @staticmethod
    def logError(message):
        Logger.log(sty.fg.red + sty.ef.bold + message + sty.rs.all)

    @staticmethod
    def logCriticalError(message):
        Logger.log(sty.fg.magenta + sty.ef.bold + message + sty.rs.all)
