from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bootstrap import seed_initial_data
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routers import admin, auth, me

app = FastAPI(title="CMU Cafeteria API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_initial_data(db)


app.include_router(auth.router)
app.include_router(me.router)
app.include_router(admin.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
