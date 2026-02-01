from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import engine, Base
from . import models  # Ensure all models (including StopArrival) are loaded before create_all
from .routes import auth, driver, passenger, admin

# Create database tables (includes stop_arrivals if missing)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bus Tracker MVP")

# CORS middleware - MUST be added before routes
# allow_credentials=False allows allow_origins=["*"] (required for wildcard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(auth.router)
app.include_router(driver.router)
app.include_router(passenger.router)
app.include_router(admin.router)

# Serve web UI (admin + passenger) from same server - use tunnel URL to avoid GitHub Pages SSL issues
_docs_path = Path(__file__).resolve().parent.parent.parent / "docs"
if _docs_path.exists():
    app.mount("/ui", StaticFiles(directory=str(_docs_path), html=True), name="ui")


@app.get("/")
def health():
    return {"status": "ok"}

