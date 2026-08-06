
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from fastapi import Request, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from models import LandInput, Blueprint
from services.ai_engine import generate_blueprint
from services.layer_sync import sync_layers

app = FastAPI(title="Smart Maps Blueprint AI")

BASE_DIR = os.path.dirname(__file__)
INDEX_PATH = os.path.join(BASE_DIR, "templates", "index.html")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for development (restrict in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/generate", response_model=Blueprint)
async def create_blueprint(input_data: LandInput):
    blueprint = generate_blueprint(input_data)
    return blueprint

@app.post("/sync-layers", response_model=Blueprint)
async def align_layers(blueprint: Blueprint):
    synced = sync_layers(blueprint)
    return synced

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return FileResponse(INDEX_PATH, media_type="text/html")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

