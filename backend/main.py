from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from backend.api.routes import router as api_router
from backend.utils.path_utils import get_resource_path
import os

app = FastAPI(title="Olive Young Crawler", version="3.0.0")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=get_resource_path("frontend/static")), name="static")

# Include API routes
app.include_router(api_router, prefix="/api")

# Templates
templates = Jinja2Templates(directory=get_resource_path("frontend/templates"))

@app.get("/")
async def serve_frontend():
    return FileResponse(get_resource_path("frontend/templates/index.html"))
