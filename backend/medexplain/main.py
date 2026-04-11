import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import extract, review, generate, cases


@asynccontextmanager
async def lifespan(app: FastAPI):
    from config import settings
    os.makedirs(settings.output_dir, exist_ok=True)
    yield


app = FastAPI(
    title="MedExplain Engine",
    description="Video generation pipeline for patient medical reports",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow the Next.js frontend on localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(extract.router)
app.include_router(review.router)
app.include_router(generate.router)
app.include_router(cases.router, prefix="/cases", tags=["cases"])


@app.get("/health")
def health():
    return {"status": "ok"}
