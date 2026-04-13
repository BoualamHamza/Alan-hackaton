from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import medical_image, chat, articles

app = FastAPI(
    title="MedBridge AI Assistant",
    description="AI assistant that explains prescriptions and medical images to patients",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(medical_image.router)
app.include_router(chat.router)
app.include_router(articles.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "MedBridge AI Assistant"}
