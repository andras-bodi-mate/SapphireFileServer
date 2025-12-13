import zipfile
import tempfile
import shutil
import random
import base64
import json
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Generator

from fastapi import FastAPI, Header
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from starlette.middleware.wsgi import WSGIMiddleware
from wsgidav.wsgidav_app import WsgiDAVApp
from wsgidav.fs_dav_provider import FilesystemProvider
from tuspyserver import create_tus_router
from preview_generator.manager import PreviewManager
from preview_generator.exception import UnsupportedMimeType
from tinytag import TinyTag
from pymediainfo import MediaInfo

from logger import Logger
from core import Core
from fileExtensions import FileExtensions

class PathCriteria:
    isFile = 1 << 0
    isDirectory = 1 << 1
    doesntExist = 1 << 2
    exists = 1 << 3

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

class PreviewRequest(BaseModel):
    path: str
    page: int

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
        self.previewCacheDirectory = self.temporaryStorageDirectory / Path("Previews")

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
            "http_authenticator": {
                "accept_basic": True,              # enable Basic authentication
                "accept_digest": False,            # disable Digest (optional, avoids conflicts)
                "default_to_digest": False
            },
            "dir_browser": {
                "enable": True,
                "response_trailer": False,
            },
            "anonymous_access": True,
        })
        self.previewManager = PreviewManager(self.previewCacheDirectory, True)

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
            path = self.directory / requestedPath
            validatePath(path, PathCriteria.exists)

            if path.is_file():
                return FileResponse(path)
                
            elif path.is_dir():
                archivePath = (self.temporaryStorageDirectory / path).with_suffix(".zip")
                if archivePath.exists():
                    archivePath.unlink()
                print("zipping...")
                with zipfile.ZipFile(archivePath, "w", zipfile.ZIP_STORED) as archive:
                    Server.addDirectoryToArchive(archive, path)
                print("zipped at", archivePath.as_posix())
                return FileResponse(archivePath)

        @self.app.get("/files/")
        @self.app.get("/files/{requestedPath:path}")
        async def getFiles(requestedPath: str = ""):
            path = (self.directory / requestedPath).resolve()
            validatePath(path, PathCriteria.isDirectory | PathCriteria.exists)
            
            return [
                {
                    "name": path.name,
                    "size": path.stat().st_size if path.is_file() else -1,
                    "lastModified": path.stat().st_mtime_ns / 1_000_000_000,
                }
                for path in path.iterdir()
                if path.absolute() == path.resolve()
            ]

        @self.app.post("/modify/")
        async def modify(request: CopyRequest | RenameRequest | DeleteRequest | NewItemRequest, mode: str = Header(...)):
            match mode:
                case "copy":
                    path = (self.directory / request.source).resolve()
                    destinationPath: Path = (self.directory / request.destination).resolve()
                    validatePath(path, PathCriteria.exists)
                    validatePath(destinationPath, PathCriteria.isDirectory | PathCriteria.exists)
                    
                    destinationPath = destinationPath / path.name
                    while destinationPath.exists():
                        destinationPath = destinationPath.with_stem(Server.getAlteredName(destinationPath.stem))

                    if path.is_file():
                        shutil.copy(path, destinationPath)
                    elif path.is_dir():
                        shutil.copytree(path, destinationPath)
                    return {"name": destinationPath.name}
                
                case "rename":
                    if len(request.newName) == 0:
                        return {"error": "New name must have a length greater than zero"}
                    path: Path = (self.directory / request.path).resolve()
                    validatePath(path, PathCriteria.exists)

                    newPath = path.with_name(request.newName)
                    if newPath.exists():
                        return {"error": "There is already a file with that name in the directory"}
                    path.rename(newPath)
                    return {"newPath": newPath.relative_to(self.directory).as_posix()}
                    
                case "delete":
                    paths: list[Path] = [(self.directory / path).resolve() for path in request.paths]
                    for path in paths:
                        validatePath(path, PathCriteria.exists)
                        
                        if path.is_file():
                            path.unlink()
                        elif path.is_dir():
                            shutil.rmtree(path)
                    return {"paths": paths}
                
                case "newFolder":
                    path = (self.directory / request.path / Path("New Folder")).resolve()
                    validatePath(path)

                    while path.exists():
                        path = path.with_stem(Server.getAlteredName(path.stem))
                    path.mkdir()
                    return {"name": path.name}

                case "newFile":
                    path = (self.directory / request.path / Path("New File")).resolve()
                    validatePath(path)

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
            validatePath(path, PathCriteria.exists)
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
            validatePath(path, PathCriteria.exists)
            stats = path.stat()
            return {
                "created": stats.st_ctime,
                "lastModified": stats.st_mtime,
                "lastAccessed": stats.st_atime
            }
        
        @self.app.get("/directorySize/{path:path}")
        async def directorySize(path: str):
            path: Path = self.directory / Path(path)
            validatePath(path, PathCriteria.isDirectory | PathCriteria.exists)
            return StreamingResponse(Server.getDirectoryInfoThrottled(path), media_type = "application/json")

        @self.app.get("/preview/{path:path}")
        async def preview(path: str, page: int = -1):
            txtVersionPath = self.previewCacheDirectory / "txtVersions" / Path(path).with_suffix(".txt")
            path: Path = self.directory / path
            validatePath(path, PathCriteria.isFile | PathCriteria.exists)
            if path.suffix[1:] == "txt":
                return FileResponse(path.as_posix(), media_type = "text/plain")
            if path.suffix[1:] in FileExtensions.documentFileExtensions or not path.suffix[1:]:
                txtVersionPath.parent.mkdir(parents = True, exist_ok = True)
                txtVersionPath.touch()
                shutil.copy(path, txtVersionPath)
                return FileResponse(txtVersionPath.as_posix(), media_type = "text/plain")
            elif path.suffix[1:] in FileExtensions.codeFileExtensions:
                txtVersionPath.parent.mkdir(parents = True, exist_ok = True)
                txtVersionPath.touch()
                shutil.copy(path, txtVersionPath)
                response = FileResponse(txtVersionPath, media_type = "text/plain")
                response.headers["X-Original-File-Extension"] = path.suffix[1:]
                return response
            else:
                try:
                    if self.previewManager.has_jpeg_preview(path.as_posix()):
                        previewPath = await run_in_threadpool(
                            lambda: self.previewManager.get_jpeg_preview(path.as_posix(), page, height = 1024)
                        )
                    elif self.previewManager.has_pdf_preview(path.as_posix()):
                        pdfPath = await run_in_threadpool(
                            lambda: self.previewManager.get_pdf_preview(path.as_posix(), page)
                        )
                        previewPath = await run_in_threadpool(
                            lambda: self.previewManager.get_jpeg_preview(pdfPath, page, height = 1024)
                        )
                    else:
                        return HTTPException(400, "Couldn't generate preview")
                except UnsupportedMimeType:
                    return HTTPException(400, "Couldn't generate preview")
                return FileResponse(previewPath, media_type = "image/jpeg")

        @self.app.get("/metadata/{path:path}")
        async def metadata(path: str):
            path: Path = self.directory / path
            validatePath(path, PathCriteria.isFile | PathCriteria.exists)
            if TinyTag.is_supported(path):
                data = TinyTag.get(path)
                return data.as_dict()
            else:
                mediaInfo = MediaInfo.parse(path.as_posix())
                data: list = mediaInfo.to_data()["tracks"]
                if len(data) <= 1:
                    return {"error": "Couldn't retrieve any additional metadata"}
                
                data = data[1:]
                mainStream = data[0]
                duration = mainStream.get("duration", None)
                width = mainStream.get("width", None)
                height = mainStream.get("height", None)
                videoCodec = mainStream.get("format", None)
                videoCodecDescription = mainStream.get("format_info", None)
                videoCodecInfo = (f"{videoCodec} ({videoCodecDescription})" if videoCodecDescription else videoCodec) if videoCodec else None
                if len(data) >= 2:
                    audioStream = data[1]
                    audioFormat = audioStream.get("format", None)
                    audioFormatDescription = audioStream.get("format_info", None)
                    audioFormatInfo = (f"{audioFormat} ({audioFormatDescription})" if audioFormatDescription else audioFormat) if audioFormat else None
                else:
                    audioFormatInfo = None

                if duration:
                    duration = str(timedelta(seconds = float(duration)/1000))
                info = {
                    "general": {
                        "Duration": duration,
                        "Resolution": f"{width} x {height}" if width and height else None,
                        "Bit rate": mainStream.get("bit_rate", None),
                        "Color space": mainStream.get("color_space", None),
                        "Bit depth": mainStream.get("bit_depth", None),
                        "Video codec": videoCodecInfo,
                        "Audio format": audioFormatInfo
                    },
                    "all": data
                }
                return info

        def validatePath(path: str | Path, criteria: int = 0):
            if not Path(path).is_relative_to(self.directory):
                raise HTTPException(400, "Invalid path")
            
            if criteria & PathCriteria.isFile and not Path(path).is_file():
                raise HTTPException(400, "Path is not a file")
            
            if criteria & PathCriteria.isDirectory and not Path(path).is_dir():
                raise HTTPException(400, "Path is not a directory")
        
            if criteria & PathCriteria.exists and not Path(path).exists():
                raise HTTPException(400, "Path doesn't exist")
            
            if criteria & PathCriteria.doesntExist and Path(path).exists():
                raise HTTPException(400, "Path already exists")

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
        Logger.logInfo("Cleaning up temporary directory...")
        shutil.rmtree(self.temporaryStorageDirectory)
        Logger.logInfo("Successfully cleaned up temporary directory")