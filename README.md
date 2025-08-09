# Project README: Multimodal Chatbot (FastAPI + React)

Overview
This project is a full-stack multimodal AI chatbot that supports:

- Text-based chat with an LLM
- Chat about user-provided images (vision + text)
- Python data analysis on user-uploaded CSVs via pandas

Stack

- Frontend: React (Vite or CRA), TypeScript (optional), fetch/axios, WebSocket (optional)
- Backend: FastAPI, Uvicorn, Pydantic, python-multipart, aiofiles, pandas
- AI Providers: Pluggable (e.g., OpenAI/other LLMs). API calls made from backend only.
- Storage/State: In-memory or Redis (optional) for sessions; local FS or object storage (optional) for files
- Deployment: Docker (optional), Nginx/Reverse proxy, HTTPS

Features

- Text Chat
  - Send user messages; receive assistant replies
  - Optional streaming responses for better UX
- Vision Chat
  - Upload an image and provide a prompt
  - The assistant analyzes the image and answers questions
- Data Analysis
  - Upload a CSV file
  - Backend parses into a pandas DataFrame
  - Ask analysis questions; assistant runs controlled pandas operations and returns results and summaries
- Session Management
  - Session ID returned on CSV upload
  - DataFrame associated with session for subsequent analysis queries
- Security and Ops
  - API keys stored on server (env vars)
  - File size/type validation
  - CORS configuration
  - Optional auth (JWT/cookies)
  - Basic rate limiting (optional)

Architecture

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
      - Fields: prompt (text), image (file)
      - Response: { reply: string }
    - POST /upload-csv (multipart/form-data)
      - Field: file (UploadFile)
      - Response: { sessionId: string, columns: string[], headPreview: any[][] }
    - POST /analyze
      - Request: { sessionId: string, question: string }
      - Response: { answer: string, artifacts?: any }
    - GET /health
      - Response: { status: "ok" }
  - Optional WebSocket:
    - /stream-chat for token streaming or proxying provider streaming
  - Data handling:
    - CSV → pandas DataFrame stored in a session registry (in-memory/Redis)
    - Cleanup on TTL or explicit endpoint (optional)

Data Flow

1. Text chat: React -> /chat -> LLM -> reply
2. Vision chat: React (FormData with prompt+image) -> /vision-chat -> multimodal LLM -> reply
3. Data analysis:
   - Upload: React (FormData file) -> /upload-csv -> DataFrame stored -> sessionId returned
   - Ask: React -> /analyze (sessionId, question) -> controlled pandas ops -> result

Project Structure

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

API Contracts

- POST /chat
  - Body: { message: string, sessionId?: string }
  - Returns: { reply: string }
- POST /vision-chat
  - multipart/form-data: prompt (string), image (file)
  - Returns: { reply: string }
- POST /upload-csv
  - multipart/form-data: file (csv)
  - Returns: { sessionId: string, columns: string[], headPreview: any[][] }
- POST /analyze
  - Body: { sessionId: string, question: string }
  - Returns: { answer: string, artifacts?: any }
- GET /health
  - Returns: { status: "ok" }

Model Provider Abstraction

- The backend uses a provider interface to support different LLM vendors:
  - Text completion/chat
  - Vision: accepts image bytes and prompt
  - Streaming: optional
- Configure via env:
  - PROVIDER=openai|...
  - PROVIDER_API_KEY=...
  - TEXT_MODEL=...
  - VISION_MODEL=...

Safety and Guardrails

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

Getting Started (Development)
Prerequisites

- Node.js LTS
- Python 3.10+
- pip/uv or Poetry
- (Optional) Redis for session store

Backend setup

- cp backend/.env.example backend/.env
  - Set PROVIDER_API_KEY, TEXT_MODEL, VISION_MODEL, allowed origins, limits, etc.
- python -m venv .venv \&\& source .venv/bin/activate
- pip install -r backend/requirements.txt
- uvicorn app.main:app --reload

Frontend setup

- cd frontend
- npm install
- cp .env.example .env
  - VITE_API_BASE_URL=http://localhost:8000
- npm run dev

Running end-to-end

- Start backend: uvicorn app.main:app --reload
- Start frontend dev server: npm run dev
- Open the app, test:
  - Text chat
  - Vision chat with an image
  - CSV upload, preview, ask analysis question

Production Deployment

- Dockerize both services
- Reverse proxy (e.g., Nginx) for TLS and routing
- Configure environment variables via secrets manager
- Object storage (S3/GCS) if persistent file storage is needed
- Observability: structured logs, metrics (Prometheus), tracing (optional)

Configuration

- Backend .env
  - PROVIDER, PROVIDER_API_KEY
  - TEXT_MODEL, VISION_MODEL
  - CORS_ALLOWED_ORIGINS
  - MAX_UPLOAD_MB
  - SESSION_BACKEND=memory|redis
  - REDIS_URL=redis://...
- Frontend .env
  - VITE_API_BASE_URL

Testing

- Backend
  - pytest for unit tests
  - httpx/TestClient for API tests
- Frontend
  - Vitest/Jest + React Testing Library
- Integration
  - E2E smoke tests for the core flows

Security Checklist

- Do not expose API keys in frontend
- Validate uploads and enforce size/type limits
- Enable HTTPS in production
- Configure CORS to known origins
- Add auth if multi-tenant/public
- Log minimally; redact sensitive data

Roadmap

- v0.1 (MVP)
  - REST endpoints, basic React UI
  - OpenAI (or chosen) text and vision models
  - CSV upload + basic analysis (describe, summary stats, simple charts returned as data URIs)
- v0.2
  - Streaming responses via WebSocket
  - Session persistence with Redis
  - Improved error messages and retries
- v0.3
  - Auth (JWT)
  - Object storage for uploads
  - Role-based rate limiting
- v0.4
  - Multi-file datasets, join/merge support
  - Basic plotting with matplotlib/altair (exported images)
  - Prompt templates for analysis tasks
- v1.0
  - Tests coverage >80%
  - CI/CD pipelines
  - Production hardening, observability
