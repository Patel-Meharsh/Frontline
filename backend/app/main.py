from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.db import Base, engine
from backend.app import models  # noqa: F401 - registers ORM tables
from backend.app.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # create_all is for local bootstrap; production schema changes will use Alembic.
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins,
                   allow_credentials=True, allow_methods=["GET", "POST", "PATCH"],
                   allow_headers=["Content-Type", "Authorization"])
app.include_router(router, prefix="/api")

@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok", "service": "frontline-api"}
