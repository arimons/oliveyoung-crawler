from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from backend.api.routes import router as api_router
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
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Include API routes
app.include_router(api_router, prefix="/api")

# Templates
templates = Jinja2Templates(directory="frontend/templates")

@app.get("/")
async def read_root():
    from starlette.requests import Request
    from starlette.responses import HTMLResponse
    # We need to mock a request object or use one if available, but for a simple return of index.html:
    # Actually, it's better to use a route that accepts Request
    return FileResponse("frontend/templates/index.html")

from fastapi.responses import FileResponse

@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/templates/index.html")
