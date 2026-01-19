from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import auth, driver, passenger, admin
from .database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bus Tracker MVP")

# CORS middleware - MUST be added before routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(auth.router)
app.include_router(driver.router)
app.include_router(passenger.router)
app.include_router(admin.router)


@app.get("/")
def health():
    return {"status": "ok"}

