import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.apps.assistant.routers import articles, chat, medical_image
from backend.apps.medexplain.api.routes import cases, extract, generate, review
from backend.apps.medexplain.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.output_dir, exist_ok=True)
    yield


app = FastAPI(
    title="Alan Hackathon Backend",
    description="Unified API for MedExplain and Assistant domains",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MedExplain domain
app.include_router(extract.router)
app.include_router(review.router)
app.include_router(generate.router)
app.include_router(cases.router, prefix="/cases", tags=["cases"])

# Assistant domain
app.include_router(chat.router)
app.include_router(medical_image.router)
app.include_router(articles.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
