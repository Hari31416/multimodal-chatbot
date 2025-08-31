from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from app.utils import create_simple_logger
from app.routes import sessions, artifacts, uploads, chat
from app.models.response_models import HealthResponse


load_dotenv()

logger = create_simple_logger(__name__)

app = FastAPI(title="Multimodal Chatbot", version="0.2.0")
# TODO: Legacy session_storage - needs to be replaced with Redis implementation
# session_storage = storage.session_storage
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")


load_dotenv()


app = FastAPI(title="Multimodal Chatbot", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(root.router)
app.include_router(sessions.router)
app.include_router(artifacts.router)
app.include_router(uploads.router)
app.include_router(chat.router)


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok")


# Simple root redirect/info
@app.get("/")
async def root():
    return {
        "message": "Multimodal Chatbot running",
    }
