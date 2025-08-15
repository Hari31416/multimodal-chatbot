from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from . import models
from .services import llm, analysis, storage, files
import uuid
import io

app = FastAPI(title="Multimodal Chatbot", version="0.1.0")

# Basic CORS (adjust via env/config in real usage)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=models.HealthResponse)
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=models.ChatResponse)
async def chat(body: models.ChatRequest):
    reply = await llm.text_completion(body.message, session_id=body.sessionId)
    return {"reply": reply}


@app.get("/start-new-chat", response_model=models.StartNewChatResponse)
async def start_new_chat():
    session_id = str(uuid.uuid4())
    return {"sessionId": session_id}


@app.get("/all-sessions", response_model=models.AllSessionsResponse)
async def all_sessions():
    sessions = storage.get_all_sessions()
    return {"sessions": sessions}


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
    session_id = str(uuid.uuid4())
    storage.put_dataframe(session_id, df)
    head_preview = df.head(5).values.tolist()
    return models.UploadCSVResponse(
        sessionId=session_id,
        columns=list(df.columns),
        headPreview=head_preview,
    )


@app.post("/analyze", response_model=models.AnalyzeResponse)
async def analyze(body: models.AnalyzeRequest):
    df = storage.get_dataframe(body.sessionId)
    if df is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    reply, artifacts = analysis.simple_question_reply(df, body.question)
    return {"reply": reply, "artifacts": artifacts}


# Simple root redirect/info
@app.get("/")
async def root():
    return {
        "message": "Multimodal Chatbot running",
        "endpoints": ["/chat", "/vision-chat", "/upload-csv", "/analyze", "/health"],
    }
