import zipfile
import tempfile
import shutil
import random
import base64
import json
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from time import sleep
from typing import Generator

from fastapi import FastAPI, Header
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from starlette.middleware.wsgi import WSGIMiddleware
from wsgidav.wsgidav_app import WsgiDAVApp
from wsgidav.fs_dav_provider import FilesystemProvider
from tuspyserver import create_tus_router

from logger import Logger
from core import Core

class SharedItem:
    idLength = 64
    customCharacters = b"-_"

    @staticmethod
    def generateNewId():
        return base64.b64encode(random.randbytes(SharedItem.idLength // 4), SharedItem.customCharacters).decode()

    def __init__(self, path: Path, expirationDate: datetime):
        self.id = SharedItem.generateNewId()
        self.path = path
        self.expirationDate = expirationDate

class CopyRequest(BaseModel):
    source: str
    destination: str

class RenameRequest(BaseModel):
    path: str
    newName: str

class DeleteRequest(BaseModel):
    paths: list[str]

class NewItemRequest(BaseModel):
    path: str

class ItemShareRequest(BaseModel):
    path: str
    expirationTime: int

@dataclass
class DirectoryInfo:
    size: int = 0
    numFiles: int = 0
    numSubdirectories: int = 0

    def toString(self):
        return json.dumps({
            "size": self.size,
            "numFiles": self.numFiles,
            "numSubdirectories": self.numSubdirectories
        }) + '\n'

class Server:
    @staticmethod
    def getDirectoryInfo(path: Path, directoryInfo = None) -> Generator[DirectoryInfo, None, None]:
        if not directoryInfo:
            directoryInfo = DirectoryInfo()
        try:
            subpaths = list(path.iterdir())
            if subpaths:
                for subpath in subpaths:
                    if subpath.is_file():
                        directoryInfo.size += subpath.stat().st_size
                        directoryInfo.numFiles += 1
                        yield directoryInfo
                    elif subpath.is_dir():
                        directoryInfo.numSubdirectories += 1
                        for info in Server.getDirectoryInfo(subpath, directoryInfo):
                            directoryInfo = info
                            yield info
            else:
                yield directoryInfo
        except PermissionError:
            yield directoryInfo
    
    @staticmethod
    def getDirectoryInfoThrottled(path: Path):
        lastUpdate = None
        lastDirectoryInfo = DirectoryInfo()
        for directoryInfo in Server.getDirectoryInfo(path):
            lastDirectoryInfo = directoryInfo
            now = datetime.now()
            if not lastUpdate or (now - lastUpdate > timedelta(seconds = 0.04)):
                lastUpdate = now
                yield directoryInfo.toString()
        yield lastDirectoryInfo.toString()

    @staticmethod
    def addDirectoryToArchive(archive: zipfile.ZipFile, rootDirectory: Path, directory: Path = None):
        if not directory:
            directory = rootDirectory
        
        for path in directory.iterdir():
            if path.is_file():
                archive.write(path, path.relative_to(rootDirectory), 0)
            elif path.is_dir():
                archive.mkdir(path.relative_to(rootDirectory).as_posix())
                Server.addDirectoryToArchive(archive, rootDirectory, path)

    @staticmethod
    def getAlteredName(originalName: str):
        defaultAlteredName = f"{originalName} (1)"

        if len(originalName) < 3:
            return defaultAlteredName
        
        if originalName[-1:] != ')':
            return defaultAlteredName
        
        previousIndexStart = -1
        for i, c in enumerate(reversed(originalName[:-1])):
            if c.isnumeric():
                previousIndexStart = len(originalName) - 2 - i
            else:
                break
        
        if previousIndexStart == -1:
            return defaultAlteredName

        if previousIndexStart != 0 and originalName[previousIndexStart - 1] != '(':
            return defaultAlteredName
        
        newIndex = int(originalName[previousIndexStart : -1]) + 1
        return f"{originalName[:previousIndexStart]}{newIndex})"

    def __init__(self, directory: Path, frontendDirectory: Path):
        if Core.projectDir.is_relative_to(directory) or Core.projectDir.is_relative_to(frontendDirectory):
            raise ValueError("Cannot serve a directory that contains the server itself")
        
        self.directory = directory
        self.directory.mkdir(parents = True, exist_ok = True)
        self.frontendDirectory = frontendDirectory
        self.temporaryStorageDirectory = Path(tempfile.mkdtemp(prefix = "SapphireFileServer"))
        self.tusDirectory = self.temporaryStorageDirectory / Path("Tus")
        self.tusLocksDirectory = self.tusDirectory / Path(".locks")

        self.app = FastAPI(lifespan = self.lifespan)
        self.davApp = WsgiDAVApp(config = {
            "mount_path": "/webdav",
            "provider_mapping": {
                "/": FilesystemProvider(self.directory)
            },
            "simple_dc": {
                "user_mapping": {
                    "*": {
                        "admin": {
                            "password": "jelszo"
                        }
                    }
                }
            },
            "dir_browser": {
                "enable": True,
                "response_trailer": False,
            },
            "anonymous_access": True,
        })

        self.sharedItems: list[SharedItem] = []

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins = ["*"],
            allow_methods = ["*"],
            allow_headers = ["*"],
            expose_headers = [
                "Location",
                "Upload-Offset",
                "Tus-Resumable",
                "Tus-Version",
                "Tus-Extension",
                "Tus-Max-Size",
                "Upload-Expires",
                "Upload-Length",
            ],
        )

        Logger.logInfo("Temporary storage location:", self.temporaryStorageDirectory.as_posix())

        @self.app.get("/download/{requestedPath:path}")
        async def download(requestedPath: str):
            path = (self.directory / requestedPath).resolve()
            if not path.is_relative_to(self.directory) or path == self.directory:
                return {"error": "Invalid path"}

            if not path.exists():
                return {"error": "File not found"}
            
            if path.is_file():
                if path.exists():
                    return FileResponse(path)
                else:
                    return {"error": "File doesn't exist"}
                
            elif path.is_dir():
                if path.exists():
                    archivePath = (self.temporaryStorageDirectory / path).with_suffix(".zip")
                    if archivePath.exists():
                        archivePath.unlink()
                    print("zipping...")
                    with zipfile.ZipFile(archivePath, "w", zipfile.ZIP_STORED) as archive:
                        Server.addDirectoryToArchive(archive, path)
                    print("zipped at", archivePath.as_posix())
                    return FileResponse(archivePath)
                else:
                    return {"error": "Directory doesn't exist"}

        @self.app.get("/files/")
        @self.app.get("/files/{requestedPath:path}")
        async def getFiles(requestedPath: str = ""):
            directoryPath = (self.directory / requestedPath).resolve()
            if not directoryPath.is_relative_to(self.directory):
                return {"error": "Invalid path"}
            if not directoryPath.exists():
                return {"error": "Directory doesn't exist"}
            
            return [
                {
                    "name": path.name,
                    "size": path.stat().st_size if path.is_file() else -1,
                    "lastModified": path.stat().st_mtime_ns / 1_000_000_000,
                }
                for path in (self.directory / requestedPath).iterdir()
                if path.absolute() == path.resolve()
            ]

        @self.app.post("/modify/")
        async def modify(request: CopyRequest | RenameRequest | DeleteRequest | NewItemRequest, mode: str = Header(...)):
            match mode:
                case "copy":
                    sourcePath = (self.directory / request.source).resolve()
                    destinationPath: Path = (self.directory / request.destination).resolve()
                    if not (sourcePath.is_relative_to(self.directory) and destinationPath.is_relative_to(self.directory)):
                        return {"error": "Invalid path"}
                    
                    if sourcePath.exists():
                        if destinationPath.exists() and destinationPath.is_dir():
                            destinationPath = destinationPath / sourcePath.name
                            while destinationPath.exists():
                                destinationPath = destinationPath.with_stem(Server.getAlteredName(destinationPath.stem))

                            if sourcePath.is_file():
                                shutil.copy(sourcePath, destinationPath)
                            elif sourcePath.is_dir():
                                shutil.copytree(sourcePath, destinationPath)
                            return {"name": destinationPath.name}
                        else:
                            return {"error": "Destination path does not exist or is not a directory"}
                    else:
                        return {"error": "Source path does not exist"}
                
                case "rename":
                    if len(request.newName) == 0:
                        return {"error": "New name must have a length greater than zero"}
                    path: Path = (self.directory / request.path).resolve()
                    if not path.is_relative_to(self.directory):
                        return {"error": "Invalid path"}

                    if path.exists():
                        newPath = path.with_name(request.newName)
                        if newPath.exists():
                            return {"error": "There is already a file with that name in the directory"}
                        path.rename(newPath)
                        return {"newPath": newPath.relative_to(self.directory).as_posix()}
                    else:
                        return {"error": "Path does not exist"}
                    
                case "delete":
                    paths: list[Path] = [(self.directory / path).resolve() for path in request.paths]
                    for path in paths:
                        if not path.is_relative_to(self.directory):
                            return {"error": "Invalid path"}
                        
                        if path.exists():
                            if path.is_file():
                                path.unlink()
                            elif path.is_dir():
                                shutil.rmtree(path)
                        else:
                            return {"error": "One of the specified paths does not exist"}
                    return {"paths": paths}
                
                case "newFolder":
                    path = (self.directory / request.path / Path("New Folder")).resolve()
                    if not path.is_relative_to(self.directory):
                        return {"error": "Invalid path"}

                    while path.exists():
                        path = path.with_stem(Server.getAlteredName(path.stem))
                    path.mkdir()
                    return {"name": path.name}

                case "newFile":
                    path = (self.directory / request.path / Path("New File")).resolve()
                    if not path.is_relative_to(self.directory):
                        return {"error": "Invalid path"}

                    while path.exists():
                        path = path.with_stem(Server.getAlteredName(path.stem))
                    path.touch()
                    return {"name": path.name}

        @self.app.get("/shared/{fileId}")
        async def getShared(fileId):
            now = datetime.now()
            for sharedItemIndex, sharedItem in reversed(tuple(enumerate(self.sharedItems))):
                if now < sharedItem.expirationDate:
                    if sharedItem.id == fileId:
                        if sharedItem.path.exists():
                            return FileResponse(sharedItem.path, filename = sharedItem.path.name)
                else:
                    self.sharedItems.pop(sharedItemIndex)

            return HTMLResponse("<html><head><title>The shared item has expired</title/></head><body>The shared item has expired.</body></html>")

        @self.app.post("/share/")
        async def share(itemShareRequest: ItemShareRequest):
            path = self.directory / itemShareRequest.path
            if not path.exists():
                return {"error": "Specified path does not exist"}
            if path.is_dir():
                archivePath = (self.temporaryStorageDirectory / "sharedDirectories" / itemShareRequest.path).with_suffix(".zip")
                archivePath.parent.mkdir(parents = True, exist_ok = True)
                with zipfile.ZipFile(archivePath, "w", zipfile.ZIP_STORED) as archive:
                    Server.addDirectoryToArchive(archive, path)
                path = archivePath

            newSharedItem = SharedItem(path, datetime.now() + timedelta(seconds = itemShareRequest.expirationTime))
            self.sharedItems.append(newSharedItem)
            return newSharedItem.id
        
        @self.app.get("/details/{path:path}")
        async def details(path: str):
            path: Path = self.directory / Path(path)
            stats = path.stat()
            return {
                "created": stats.st_ctime,
                "lastModified": stats.st_mtime,
                "lastAccessed": stats.st_atime
            }
        
        @self.app.get("/directorySize/{path:path}")
        async def directorySize(path: str):
            path: Path = self.directory / Path(path)
            return StreamingResponse(Server.getDirectoryInfoThrottled(path), media_type = "application/json")

        def validateUpload(metadata: dict, uploadInfo: dict):
            if "filename" not in metadata or "directory" not in metadata:
                raise HTTPException(status_code = 400, detail = "Filename or directory is missing")
            
        def finishUpload(filePathStr: str, metadata: dict):
            print("Upload complete")
            filePath = Path(filePathStr)
            newPath: Path = self.directory / metadata["directory"] / metadata["filename"]
            print(newPath.as_posix())
            if not newPath.resolve().is_relative_to(self.directory):
                return {"error": "Invalid path"}
            newPath.parent.mkdir(parents = True, exist_ok = True)
            if newPath.exists():
                newPath = newPath.with_stem(Server.getAlteredName(newPath.stem))
            shutil.move(filePath, newPath)

        self.app.include_router(
            create_tus_router(
                prefix = "upload",
                files_dir = self.tusDirectory.as_posix(),
                pre_create_hook = validateUpload,
                on_upload_complete = finishUpload,
            )
        )
        self.app.mount("/webdav", WSGIMiddleware(self.davApp))
        self.app.mount("/", StaticFiles(directory = Core.getPath("frontend/dist"), html = True), name = "static")

    def lifespan(self, app: FastAPI):
        yield
        shutil.rmtree(self.temporaryStorageDirectory)
        Logger.logInfo("Cleaning up temporary directory")