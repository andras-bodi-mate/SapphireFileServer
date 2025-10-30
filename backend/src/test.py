from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import uvicorn

app = FastAPI()
app.mount(
    "/res",
    StaticFiles(
        directory=r"C:\Users\bodit\Documents\WebProjects\SapphireFileServer\frontend\res"
    ),
    name="res",
)

uvicorn.run(app, host="127.0.0.1", port=8000)
