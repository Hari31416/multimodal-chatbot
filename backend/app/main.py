from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from app.models import models
from app.services import storage, llm


load_dotenv()

app = FastAPI(title="Multimodal Chatbot", version="0.2.0")
session_storage = storage.session_storage
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")


from app.routes import sessions, artifacts, uploads
from app.models.response_models import HealthResponse


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


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok")


@app.post("/chat", response_model=models.ChatResponse)
async def chat(body: models.ChatRequest):
    reply = await llm.text_completion(body.message, session_id=body.sessionId)
    return {"reply": reply}


@app.post("/all-previous-chats", response_model=models.AllChatResponse)
async def all_previous_chats(sessionId: str = Form(...)):
    messages = session_storage.get_messages(sessionId)
    if not messages:
        messages = []
    # remove the system message if it exists
    messages = [msg for msg in messages if msg["role"] != "system"]

    return models.AllChatResponse(
        sessionId=sessionId,
        messages=[
            models.OneChatMessage(role=msg["role"], content=msg["content"])
            for msg in messages
        ],
    )


@app.post("/delete-session", response_model=models.DeleteSessionResponse)
async def delete_session(sessionId: str = Form(...)):
    if not session_storage.delete_session(sessionId):
        print(f"Session {sessionId} not found or already deleted")
        return {"message": "Session not found or already deleted"}
    return {"message": "Session deleted successfully"}


@app.post("/vision-chat", response_model=models.ChatResponse)
async def vision_chat(
    message: str = Form(...),
    image: UploadFile = File(...),
    sessionId: str | None = Form(None),
):
    # Basic validation
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    image_bytes = await image.read()
    reply = await llm.vision_completion(
        message=message, image_bytes=image_bytes, session_id=sessionId
    )
    return {"reply": reply}


@app.post("/analyze", response_model=models.AnalyzeResponse)
async def analyze(body: models.AnalyzeRequest):
    df = session_storage.get_dataframe(body.sessionId)
    if df is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    res = await llm.analyze_data(df=df, message=body.message, session_id=body.sessionId)
    return res


# Simple root redirect/info
@app.get("/")
async def root():
    return {
        "message": "Multimodal Chatbot running",
    }
