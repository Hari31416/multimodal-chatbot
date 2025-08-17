# Multimodal Chatbot

## Overview

This project is a full-stack multimodal AI chatbot that supports:

- Text-based chat with an LLM
- Chat about user-provided images (vision + text)
- Python data analysis on user-uploaded CSVs via pandas

## Stack

- Frontend: React (Vite or CRA), TypeScript (optional), fetch/axios, WebSocket (optional)
- Backend: FastAPI, Uvicorn, Pydantic, python-multipart, aiofiles, pandas
- AI Providers: Pluggable (e.g., OpenAI/other LLMs). API calls made from backend only.
- Storage/State: In-memory or Redis (optional) for sessions; local FS or object storage (optional) for files
- Deployment: Docker (optional), Nginx/Reverse proxy, HTTPS

## Features

- Text Chat
  - Send user messages; receive assistant replies
  - Optional streaming responses for better UX
- Vision Chat
  - Upload an image and provide a message (text + image multimodal)
  - The assistant analyzes the image and answers questions
- Data Analysis
  - Upload a CSV file
  - Backend parses into a pandas DataFrame
  - Ask analysis questions; assistant runs controlled pandas operations and returns results and summaries
- Session Management
  - Session ID returned on CSV upload or via GET /start-new-chat
  - DataFrame and message history associated with session for subsequent analysis and chat queries
  - Sidebar lists prior sessions (cached client-side with short TTL) and allows switching
  - Delete individual sessions via POST /delete-session
  - GET /all-sessions returns currently active (non-expired) session IDs plus optional titles
- Security and Ops
  - API keys stored on server (env vars)
  - File size/type validation
  - CORS configuration
  - Optional auth (JWT/cookies)
  - Basic rate limiting (optional)

## Architecture

- Frontend (React)
  - Pages/Components:
    - Chat: text chat UI with history
    - VisionChat: prompt + image upload
    - DataUpload: CSV upload, preview columns/head
    - DataAnalyze: question input referencing uploaded dataset by sessionId
    - Optional: Streaming UI using WebSocket
  - State:
    - chatHistory
    - sessionId (from /upload-csv)
    - previews (columns, head)
- Backend (FastAPI)
  - REST Endpoints:
    - POST /chat
      - Request: { message: string, sessionId?: string }
      - Response: { reply: string }
    - POST /vision-chat (multipart/form-data)
      - Fields: message (text), image (file), optionally sessionId (text)
      - Response: { reply: string }
    - POST /upload-csv (multipart/form-data)
      - Field: file (UploadFile)
      - Response: { sessionId: string, columns: string[], headPreview: any[][] }
    - POST /analyze
      - Request: { sessionId: string, question: string }
      - Response: { reply: string, artifact?: any }
    - GET /start-new-chat
      - Response: { sessionId: string }
    - GET /all-sessions
      - Response: { sessionIds: string[], titles: string[] }
    - POST /delete-session (multipart/form-data)
      - Fields: sessionId (text)
      - Response: { message: string }
    - GET /health
      - Response: { status: "ok" }
  - Optional WebSocket:
    - /stream-chat for token streaming or proxying provider streaming
  - Data handling:
    - CSV → pandas DataFrame stored in a session registry (in-memory/Redis)
    - Cleanup on TTL or explicit endpoint (optional)

## Data Flow

1. Text chat: React -> /chat -> LLM -> reply
2. Vision chat: React (FormData with prompt+image) -> /vision-chat -> multimodal LLM -> reply
3. Data analysis:
   - Upload: React (FormData file) -> /upload-csv -> DataFrame stored -> sessionId returned
   - Ask: React -> /analyze (sessionId, question) -> controlled pandas ops -> result

## Project Structure

- /frontend
  - src/
    - components/
      - Chat.tsx
      - VisionChat.tsx
      - DataUpload.tsx
      - DataAnalyze.tsx
    - api/
      - client.ts (fetch/axios)
    - pages/
      - Home.tsx
    - App.tsx
    - main.tsx
  - package.json
  - .env (frontend config like API base URL)
- /backend
  - app/
    - main.py (FastAPI app and routes)
    - models.py (Pydantic schemas)
    - services/
      - llm.py (text + vision model calls)
      - analysis.py (pandas helpers, safe ops)
      - storage.py (session store, Redis optional)
      - files.py (upload handling)
    - config.py
    - deps.py (CORS, middleware)
  - requirements.txt or pyproject.toml
  - .env (server secrets like API keys)
- docker/
  - Dockerfile.backend
  - Dockerfile.frontend
  - docker-compose.yml (optional)
- README.md (this file)

## API Contracts

- POST /chat
  - Body: { message: string, sessionId?: string }
  - Returns: { reply: string }
- POST /vision-chat
  - multipart/form-data: message (string), image (file), sessionId? (string)
  - Returns: { reply: string }
- POST /upload-csv
  - multipart/form-data: file (csv)
  - Returns: { sessionId: string, columns: string[], headPreview: any[][] }
- POST /analyze
  - Body: { sessionId: string, question: string }
  - Returns: { reply: string, artifact?: any }
- GET /start-new-chat
  - Returns: { sessionId: string }
- GET /all-sessions
  - Returns: { sessionIds: string[], titles: string[] }
- POST /delete-session
  - multipart/form-data: sessionId (string)
  - Returns: { message: string }
- GET /health
  - Returns: { status: "ok" }

## Model Provider & LLM Integration

- The backend now uses [litellm](https://github.com/BerriAI/litellm) for a unified async interface to multiple providers.
- Supports multimodal (image+text) messages for vision.
- Message history is stored per session (truncated for context window / performance).
- Configure via env:
  - LLM_MODEL=<provider/model-id> (e.g., gemini/gemini-2.0-flash)
  - PROVIDER_API_KEY=<key> (or provider-specific keys litellm will read)
  - (Optional) Additional provider-specific env vars supported by litellm

## Safety and Guardrails

- File uploads
  - Enforce content-type and size limits (e.g., max 10–20 MB)
  - Only CSV for data analysis; images for vision chat
- Data analysis sandbox
  - Whitelist safe pandas operations
  - Avoid arbitrary code execution
  - Limit rows processed for previews
- PII and secrets
  - Do not log raw uploads or API keys
- Rate limiting and auth
  - Optional middleware for IP/user-based limits
  - JWT/cookie auth if exposed publicly
- Cleanup
  - Session/DataFrame TTL (e.g., 30–120 minutes)
  - Background task to evict expired sessions

## Breaking Changes (Latest)

- Vision endpoint form field renamed: prompt -> message
- Analyze response field renamed: answer -> reply
- New endpoints added: /start-new-chat, /all-sessions, /delete-session
- /all-sessions response shape changed to { sessionIds, titles }
- Pydantic upgraded to v2 (schema / validation differences vs v1)

## Getting Started (Development)

### Prerequisites

- Node.js LTS
- Python 3.10+
- pip/uv or Poetry
- (Optional) Redis for session store

### Backend setup

- cp backend/.env.example backend/.env
  - Set PROVIDER_API_KEY, TEXT_MODEL, VISION_MODEL, allowed origins, limits, etc.
- python -m venv .venv \&\& source .venv/bin/activate
- pip install -r backend/requirements.txt (includes litellm, rich, e2b-code-interpreter)
- uvicorn app.main:app --reload

### Frontend setup

- cd frontend
- npm install
- cp .env.example .env
  - VITE_API_BASE_URL=http://localhost:8000
- npm run dev

### Optional Sandbox / Code Execution (Experimental)

The project includes an e2b sandbox utility (`services/e2b_utils.py`) for executing Python code safely (e.g., future data analysis expansions). This is currently optional and not invoked by core endpoints.

### Running end-to-end

- Start backend: uvicorn app.main:app --reload
- Start frontend dev server: npm run dev
- Open the app, test:
  - Text chat
  - Vision chat with an image
  - CSV upload, preview, ask analysis question
  - Delete a previous chat session from sidebar

### Production Deployment

- Dockerize both services
- Reverse proxy (e.g., Nginx) for TLS and routing
- Configure environment variables via secrets manager
- Object storage (S3/GCS) if persistent file storage is needed
- Observability: structured logs, metrics (Prometheus), tracing (optional)

### Configuration

- Backend .env
  - PROVIDER, PROVIDER_API_KEY
  - TEXT_MODEL, VISION_MODEL
  - CORS_ALLOWED_ORIGINS
  - MAX_UPLOAD_MB
  - SESSION_BACKEND=memory|redis
  - REDIS_URL=redis://...
- Frontend .env
  - VITE_API_BASE_URL

### Security Checklist

- Do not expose API keys in frontend
- Validate uploads and enforce size/type limits
- Enable HTTPS in production
- Configure CORS to known origins
- Add auth if multi-tenant/public
- Log minimally; redact sensitive data

## Recent Frontend Enhancements

- Lazy loading & idle decoding for large base64 vision images.
- Unified sidebar with cached session list and per-session delete action.
- Data analysis history reconstruction: JSON strings containing `{explanation, code, plot}` parsed into explanation + code (plot ignored for history until backend persists image data URIs).
- Vision multimodal history parsing for list-of-parts structure.
- Robust code + math rendering with graceful fallback for unknown languages.

## Session Deletion Flow

1. User opens sidebar (or hovers a session row on desktop).
2. Delete icon appears; confirmation prompt guards accidental removal.
3. POST /delete-session executed (FormData: sessionId).
4. UI optimistically removes session; if active session deleted, a fresh session is started.

## Analysis History Parsing

Restored messages matching the serialized object shape:

```json
{ "explanation": "...", "code": "...", "plot": "plot_created" }
```

are rendered with:

- Explanation (natural language)
- Code block (Python)

The `plot` placeholder is ignored for history until actual plot data URIs are stored.

## Future Improvements

- Persist and display generated plots in history (data URIs) with lazy loading.
- Automatic session title generation from first user prompt or analysis summary.
- Bulk delete & undo (soft delete grace window).
- Streaming token updates for long responses.
