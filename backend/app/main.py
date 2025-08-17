from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from . import models
from .services import redis_storage, llm, files
from .endpoint_utils import start_new_session, get_session_info, get_all_sessions_info
import io


load_dotenv()

app = FastAPI(title="Multimodal Chatbot", version="0.2.0")
session_storage = redis_storage.session_storage
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Basic CORS (adjust via env/config in real usage)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=models.HealthResponse)
async def health():
    return {"status": "ok"}


@app.get("/start-new-chat", response_model=models.StartNewChatResponse)
async def start_new_chat():
    session_id = start_new_session()
    return {"sessionId": session_id}


@app.post("/session-info", response_model=models.SessionInfo)
async def session_info(sessionId: str):
    return get_session_info(sessionId)


@app.get("/all-sessions", response_model=models.AllSessionsResponse)
async def all_sessions():
    return get_all_sessions_info()


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
        raise HTTPException(status_code=404, detail="Session not found or expired")
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


@app.post("/upload-csv", response_model=models.UploadCSVResponse)
async def upload_csv(file: UploadFile = File(...)):
    if file.content_type not in (
        "text/csv",
        "application/vnd.ms-excel",
        "application/octet-stream",
    ):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    raw_bytes = await file.read()
    df = files.load_csv(io.BytesIO(raw_bytes))
    session_id = start_new_session()
    session_storage.put_dataframe(session_id, df)
    head_preview = df.head(5).values.tolist()
    return models.UploadCSVResponse(
        sessionId=session_id,
        columns=list(df.columns),
        headPreview=head_preview,
    )


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
