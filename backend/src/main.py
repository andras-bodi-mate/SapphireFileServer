from pathlib import Path

import uvicorn

from logger import Logger
from server import Server
from core import Core

def main():
    Logger.logInfo("Program started")
    server = Server(Path.home() / Path("Downloads/Python Projects"), Core.getPath("frontend/dist"))
    uvicorn.run(server.app, host = "0.0.0.0", port = 8000, ssl_keyfile = Core.getPath("backend/keyFile.pem"), ssl_certfile = Core.getPath("backend/certFile.pem"))

if __name__ == "__main__":
    main()
