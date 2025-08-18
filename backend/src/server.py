from pathlib import Path
import zipfile
import tempfile
import shutil

from fastapi import FastAPI, Header, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from staticFiles import NoCacheStaticFiles
from core import Core

class CopyRequest(BaseModel):
    source: str
    destination: str

class RenameRequest(BaseModel):
    path: str
    newName: str

class DeleteRequest(BaseModel):
    paths: list[str]

class Server:
    @staticmethod
    def getDirectorySize(path: Path):
        size = 0
        try:
            for p in path.iterdir():
                if p.is_file():
                    size += p.stat().st_size
                elif p.is_dir():
                    size += Server.getDirectorySize(p)
        except PermissionError:
            pass
        return size
    
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

    def __init__(self, directory: Path):
        self.directory = directory
        self.directory.mkdir(parents = True, exist_ok = True)
        self.temporaryStorage = Path(tempfile.mkdtemp(prefix = "SapphireFileServer"))

        self.app = FastAPI()

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://localhost:8080",   # your Vite dev server
                "http://127.0.0.1:8080",  # just in case
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @self.app.post("/upload/")
        async def uploadFile(uploadedFile: UploadFile):
            filePath = directory / uploadedFile.filename

            with open(filePath, "wb") as file:
                file.write(await uploadedFile.read())

            return {"filename": uploadedFile.filename}

        @self.app.get("/download/{requestedPath:path}")
        async def download(requestedPath: str):
            path = self.directory / requestedPath

            if not path.exists():
                return {"error": "File not found"}
            
            if path.is_file():
                if path.exists():
                    return FileResponse(path)
                else:
                    return {"error": "File doesn't exist"}
                
            elif path.is_dir():
                if path.exists():
                    archivePath = (self.temporaryStorage / path.name).with_suffix(".zip")
                    print("zipping...")
                    with zipfile.ZipFile(archivePath, "w", zipfile.ZIP_STORED) as archive:
                        Server.addDirectoryToArchive(archive, path)
                    print("zipped")
                    return FileResponse(archivePath)
                else:
                    return {"error": "Directory doesn't exist"}

        @self.app.get("/files/")
        @self.app.get("/files/{requestedPath:path}")
        async def getFiles(requestedPath: str = ""):
            directoryPath = self.directory / requestedPath
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
        async def modify(request: CopyRequest | RenameRequest | DeleteRequest, mode: str = Header(...)):
            match mode:
                case "copy":
                    sourcePath = self.directory / request.source
                    destinationPath: Path = self.directory / request.destination
                    if sourcePath.exists():
                        if destinationPath.exists() and destinationPath.is_dir():
                            destinationPath = destinationPath / sourcePath.name
                            while destinationPath.exists():
                                destinationPath = destinationPath.with_stem(Server.getAlteredName(destinationPath.stem))

                            if sourcePath.is_file():
                                shutil.copy(sourcePath, destinationPath)
                            elif sourcePath.is_dir():
                                shutil.copytree(sourcePath, destinationPath)
                        else:
                            return {"error": "Destination path does not exist or is not a directory"}
                    else:
                        return {"error": "Source path does not exist"}
                
                case "rename":
                    if len(request.newName) == 0:
                        return {"error": "New name must have a length greater than zero"}

                    path = self.directory / request.path
                    if path.exists():
                        path.rename(path.with_name(request.newName))
                    else:
                        return {"error": "Path does not exist"}
                    
                case "delete":
                    paths = [self.directory / path for path in request.paths]
                    for path in paths:
                        if path.exists():
                            if path.is_file():
                                path.unlink()
                            elif path.is_dir():
                                shutil.rmtree(path)
                        else:
                            return {"error": "One of the specified paths does not exist"}

        self.app.mount(
            "/",
            NoCacheStaticFiles(
                directory=Core.getPath("frontend/dist").as_posix(), html=True
            ),
            name="static",
        )
