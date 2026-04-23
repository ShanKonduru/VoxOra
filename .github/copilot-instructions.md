# VoxOra — Project Guidelines

## Overview
Voxora is an AI-enabled interactive voice survey platform.
- **Backend**: Python 3.12+, FastAPI 0.111+, SQLAlchemy 2.x async, PostgreSQL 16, Redis 7
- **Frontend**: React 18, Vite 5, Tailwind CSS 3, Zustand 4, Axios 1
- **AI**: OpenAI GPT-4o (chat), Whisper (STT), TTS-1-HD (speech), text-moderation-stable
- **Voice**: Browser WebRTC → MediaRecorder (WebM/Opus) → WebSocket binary → Whisper → GPT-4o → TTS → streamed MP3

## Architecture

| Layer | Location | Notes |
|---|---|---|
| REST API | `backend/app/api/` | One file per domain (`auth`, `surveys`, `participants`, `sessions`, `admin`) |
| WebSocket | `backend/app/api/websocket.py` | Single endpoint `/ws/session/{session_id}` |
| Services | `backend/app/services/` | Business logic; no direct DB access from API routes |
| Security | `backend/app/security/` | `auth.py`, `input_sanitizer.py`, `rate_limiter.py` |
| Prompts | `backend/app/prompts/` | AI prompt builders; never embed raw strings in service code |
| React hooks | `frontend/src/hooks/` | All stateful logic lives here — components are thin |
| Zustand stores | `frontend/src/store/` | `sessionStore` (voice session state), `adminStore` (JWT, sessionStorage) |
| Services | `frontend/src/services/` | `api.js` (Axios), `websocketClient.js` (WS factory) |

## Build & Test

```bash
# Backend
cd backend
pip install -r requirements-dev.txt
pytest --cov=app tests/ -q
ruff check .
black --check .

# Frontend
cd frontend
npm ci
npm run build
```

## Critical Conventions
See the detailed instruction files in `.github/instructions/` for:
- Backend async patterns → `backend-conventions.instructions.md`
- Frontend hooks/store patterns → `frontend-conventions.instructions.md`
- Security rules → `security-patterns.instructions.md`
- Voice/audio pipeline → `voice-pipeline.instructions.md`
