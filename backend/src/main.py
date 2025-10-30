from pathlib import Path

import uvicorn

from logger import Logger
from server import Server


def main():
    Logger.logInfo("Program started")
    server = Server(Path.home())
    uvicorn.run(server.app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    main()
