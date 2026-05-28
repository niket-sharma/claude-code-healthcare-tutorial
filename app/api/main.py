from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.db import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="CareTriage API", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}
