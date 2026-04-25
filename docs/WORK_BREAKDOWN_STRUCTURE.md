# Voxora — Work Breakdown Structure (WBS)
## Epics, Features, User Stories & Task-Level Effort Estimates

> **Estimation Scale:** Story Points (Fibonacci) — 1 SP ≈ 0.5 day of engineering effort for a mid-senior engineer  
> **Effort Key:** SP = Story Points | D = Days | W = Weeks  
> **Complexity Labels:** XS (1–2 SP) | S (3 SP) | M (5 SP) | L (8 SP) | XL (13 SP)
> **Task Status Markers:** `[DONE]` completed | `[PARTIAL]` implemented in part | `[PENDING]` not yet started

---

## WBS Summary Table

> **Updated April 2026:** All epics (E1–E6, E8) have been scaffolded and committed to `master`.  
> E7 (Integration & Testing) and E9 equivalent (UAT/Load Testing) remain pending a live environment.

| Epic | Name | Total SP | Est. Duration | Status |
|---|---|---|---|---|
| E1 | Project Foundation | 42 SP | 2 weeks | ✅ Done |
| E2 | Backend API & Database | 89 SP | 4 weeks | In Progress (hardening underway) |
| E3 | AI Orchestration Engine | 97 SP | 5 weeks | ✅ Done (scaffolding) |
| E4 | Frontend Participant Experience | 76 SP | 5 weeks | ✅ Done (scaffolding) |
| E5 | Security Hardening | 68 SP | 4 weeks | In Progress (rate-limit and auth transport updates) |
| E6 | Admin Dashboard | 64 SP | 4 weeks | ✅ Done (scaffolding) |
| E7 | Integration & Testing | 55 SP | 4 weeks | In Progress (focused backend contracts validated) |
| E8 | DevOps & Deployment | 52 SP | 4 weeks | ✅ Done (scaffolding) |
| **TOTAL** | | **543 SP** | **~28 weeks** | |

---

## Epic 1 — Project Foundation ✅ Done

**Goal:** Establish a zero-ambiguity engineering starting point. Every team member can clone and run the full environment within 30 minutes.  
**Total Effort:** 42 SP (~2 weeks)  
**Completed:** April 2026

---

### Feature 1.1 — Repository & Code Standards Setup
**Effort:** 10 SP

#### User Story 1.1.1
> **As a** developer,  
> **I want** a monorepo with a clear directory structure,  
> **so that** I know exactly where to find and place code.

**Acceptance Criteria:**
- Root directories `/backend`, `/frontend`, `/nginx`, `/.github` exist with README stubs
- `.gitignore` covers Python, Node, IDE files, and `.env` files
- `.editorconfig` enforces consistent indentation (2 spaces JS/JSX, 4 spaces Python)
- `README.md` at root contains setup instructions

| Task | Description | SP | Complexity |
|---|---|---|---|
| T1.1.1.1 | Initialize Git repo, configure branch protection on `main` and `develop` | 1 | XS |
| T1.1.1.2 | Create monorepo directory structure with stub files | 1 | XS |
| T1.1.1.3 | Write `.gitignore`, `.editorconfig`, root `README.md` placeholder | 1 | XS |
| T1.1.1.4 | Configure pre-commit hooks: `black`, `ruff`, `eslint` | 2 | S |
| T1.1.1.5 | Document branching strategy and PR template | 1 | XS |
| **Subtotal** | | **6 SP** | |

#### User Story 1.1.2
> **As a** developer,  
> **I want** automated code quality checks on every pull request,  
> **so that** code style and basic errors are caught before review.

| Task | Description | SP | Complexity |
|---|---|---|---|
| T1.1.2.1 | Write GitHub Actions `ci.yml`: backend lint + test job `[DONE]` | 2 | S |
| T1.1.2.2 | Write GitHub Actions `ci.yml`: frontend lint + build job `[DONE]` | 2 | S |
| T1.1.2.3 | Expand PR workflow trigger to `main` + `develop` `[DONE]` | 1 | XS |
| T1.1.2.4 | Add focused backend contract test job in CI `[DONE]` | 1 | XS |
| **Subtotal** | | **6 SP** | |

---

### Feature 1.2 — Local Development Environment
**Effort:** 18 SP

#### User Story 1.2.1
> **As a** developer,  
> **I want** to start all services with a single `docker compose up` command,  
> **so that** I can focus on coding rather than environment setup.

**Acceptance Criteria:**
- `docker compose up --build` starts Postgres, Redis, backend, and frontend with no errors
- Backend hot-reload works (code changes reflected without container restart)
- Frontend hot-reload works (code changes reflected in browser without full rebuild)
- Services communicate on a shared Docker network

| Task | Description | SP | Complexity |
|---|---|---|---|
| T1.2.1.1 | Write `docker-compose.yml` with Postgres 16 service, volume, health check | 2 | S |
| T1.2.1.2 | Add Redis 7 service with volume to `docker-compose.yml` | 1 | XS |
| T1.2.1.3 | Write backend `Dockerfile` (dev): Python 3.12, pip install, hot reload | 2 | S |
| T1.2.1.4 | Write frontend `Dockerfile` (dev): Node 20, npm install, Vite dev server | 2 | S |
| T1.2.1.5 | Configure shared Docker network and inter-service environment variables | 2 | S |
| T1.2.1.6 | Write `docker-compose.prod.yml` skeleton with Nginx service | 2 | S |
| T1.2.1.7 | Verify and document local setup steps in `README.md` | 1 | XS |
| **Subtotal** | | **12 SP** | |

#### User Story 1.2.2
> **As a** developer,  
> **I want** a database seeding script,  
> **so that** I can start development with realistic test data immediately.

| Task | Description | SP | Complexity |
|---|---|---|---|
| T1.2.2.1 | Write `seed.py`: create 1 survey, 5 questions, 10 participants | 3 | S |
| T1.2.2.2 | Add seed script to `docker-compose.yml` as a one-shot init service | 3 | S |
| **Subtotal** | | **6 SP** | |

---

### Feature 1.3 — Backend Application Scaffold
**Effort:** 8 SP

#### User Story 1.3.1
> **As a** backend engineer,  
> **I want** a FastAPI application that starts cleanly and serves a health endpoint,  
> **so that** I have a verified foundation to build on.

| Task | Description | SP | Complexity |
|---|---|---|---|
| T1.3.1.1 | Initialize FastAPI app factory in `main.py` with lifespan events (startup/shutdown) | 2 | S |
| T1.3.1.2 | Implement Pydantic `Settings` class with all env var definitions and defaults | 2 | S |
| T1.3.1.3 | Implement `GET /health` endpoint returning `{"status": "ok", "version": "..."}` | 1 | XS |
| T1.3.1.4 | Set up `requirements.txt` and `requirements-dev.txt` with pinned versions | 1 | XS |
| T1.3.1.5 | Configure Alembic: `alembic.ini`, `env.py` connected to SQLAlchemy async engine | 2 | S |
| **Subtotal** | | **8 SP** | |

---

### Feature 1.4 — Frontend Application Scaffold
**Effort:** 6 SP

#### User Story 1.4.1
> **As a** frontend engineer,  
> **I want** a React + Vite app with routing and Tailwind configured,  
> **so that** I can build pages immediately without setup overhead.

| Task | Description | SP | Complexity |
|---|---|---|---|
| T1.4.1.1 | Initialize React + Vite project, configure `vite.config.js` | 1 | XS |
| T1.4.1.2 | Install and configure Tailwind CSS with `tailwind.config.js` | 1 | XS |
| T1.4.1.3 | Set up React Router v6 with placeholder routes | 2 | S |
| T1.4.1.4 | Configure Axios instance with base URL, request interceptors | 1 | XS |
| T1.4.1.5 | Install and configure Zustand, create empty store files | 1 | XS |
| **Subtotal** | | **6 SP** | |

---

## Epic 2 — Backend API & Database ✅ Done (scaffolding)

**Goal:** Complete, tested, and documented REST API with full database schema. Admin authentication working.  
**Total Effort:** 89 SP (~4 weeks)  
**Completed:** April 2026

---

### Feature 2.1 — Database Schema & ORM Models
**Effort:** 22 SP

#### User Story 2.1.1
> **As a** backend engineer,  
> **I want** ORM models and Alembic migrations for all core entities,  
> **so that** the database schema is version-controlled and reproducible.

**Acceptance Criteria:**
- All tables created by running `alembic upgrade head` on an empty database
- All foreign key constraints enforced
- All required indexes created
- Migrations are reversible (`alembic downgrade -1` works)

| Task | Description | SP | Complexity |
|---|---|---|---|
| T2.1.1.1 | Implement `Survey` SQLAlchemy model with all columns and constraints | 2 | S |
| T2.1.1.2 | Implement `Question` model with FK to `Survey`, unique constraint on `(survey_id, order_index)` | 3 | S |
| T2.1.1.3 | Implement `Participant` model with status enum, invite_token unique index | 3 | S |
| T2.1.1.4 | Implement `Session` model with persona JSONB, state enum, FK to Participant | 3 | S |
| T2.1.1.5 | Implement `Response` model with all transcript, sentiment, and moderation fields | 3 | S |
| T2.1.1.6 | Implement `AdminUser` model with hashed_password field | 2 | S |
| T2.1.1.7 | Write Alembic migration for initial schema (all 6 tables) | 3 | S |
| T2.1.1.8 | Write performance indexes migration (status, invite_token, FKs) | 2 | S |
| T2.1.1.9 | Write Pydantic schemas for all models (request + response shapes) | 3 | S |
| **Subtotal** | | **24 SP** | |

---

### Feature 2.2 — Survey & Question CRUD API
**Effort:** 16 SP

#### User Story 2.2.1
> **As an** admin,  
> **I want** to create and manage surveys with questions via API,  
> **so that** I can set up interview scripts without database access.

**Acceptance Criteria:**
- Full CRUD for surveys and questions
- Questions maintain `order_index` correctly on create/update
- Soft-delete for surveys (sets `is_active = false`, does not destroy data)
- All endpoints documented in Swagger UI

| Task | Description | SP | Complexity |
|---|---|---|---|
| T2.2.1.1 | Implement `POST /api/surveys` with nested question creation | 3 | S |
| T2.2.1.2 | Implement `GET /api/surveys` with pagination | 2 | S |
| T2.2.1.3 | Implement `GET /api/surveys/{id}` with questions list | 1 | XS |
| T2.2.1.4 | Implement `PUT /api/surveys/{id}` | 2 | S |
| T2.2.1.5 | Implement `DELETE /api/surveys/{id}` (soft delete) | 1 | XS |
| T2.2.1.6 | Implement `POST /api/surveys/{id}/questions` | 2 | S |
| T2.2.1.7 | Implement `PUT /api/surveys/{id}/questions/{q_id}` | 2 | S |
| T2.2.1.8 | Implement `DELETE /api/surveys/{id}/questions/{q_id}` with order rebalancing | 3 | S |
| **Subtotal** | | **16 SP** | |

---

### Feature 2.3 — Participant Management API
**Effort:** 14 SP

#### User Story 2.3.1
> **As an** admin,  
> **I want** to bulk-create participants and generate their unique survey links,  
> **so that** I can onboard a cohort of participants quickly.

| Task | Description | SP | Complexity |
|---|---|---|---|
| T2.3.1.1 | Implement `POST /api/participants` (single or bulk, accepts list of `{email, name}`) | 5 | M |
| T2.3.1.2 | Implement invite token generation (UUID v4) and URL formatter | 2 | S |
| T2.3.1.3 | Implement `GET /api/participants` with pagination, status filter, search | 3 | S |
| T2.3.1.4 | Implement `GET /api/participants/{id}` with session history | 2 | S |
| T2.3.1.5 | Implement `PATCH /api/participants/{id}/status` (manual status override by admin) | 2 | S |
| **Subtotal** | | **14 SP** | |

---

### Feature 2.4 — Session Management API
**Effort:** 18 SP

#### User Story 2.4.1
> **As a** participant,  
> **I want** to open my survey link and have a session automatically prepared for me,  
> **so that** I can begin the interview immediately without any account setup.

**Acceptance Criteria:**
- Valid invite token → session created → session JWT returned in < 500ms
- Already-completed token → `409` with "Survey already completed" message
- In-progress token → existing session returned (reconnect flow)
- Invalid token → `404`
- Expired token → `410 Gone`

| Task | Description | SP | Complexity |
|---|---|---|---|
| T2.4.1.1 | Implement `POST /api/sessions/init`: validate token, check status, create session `[PARTIAL]` | 5 | M |
| T2.4.1.2 | Implement persona assignment on session init (calls `PersonaManager`) | 3 | S |
| T2.4.1.3 | Implement session JWT generation (short-lived, session-scoped) | 2 | S |
| T2.4.1.4 | Implement Redis session state write on init | 2 | S |
| T2.4.1.5 | Implement `GET /api/sessions/{id}`: return current state for reconnection `[PARTIAL]` | 2 | S |
| T2.4.1.6 | Handle all edge cases: COMPLETED, IN_PROGRESS, EXPIRED, FLAGGED `[PARTIAL]` | 3 | S |
| T2.4.1.7 | Write unit tests for all session init edge cases (6 scenarios) `[PARTIAL]` | 3 | S |
| T2.4.1.8 | Align session response contract fields (`started_at`, `state`, required payload fields) `[DONE]` | 2 | S |
| **Subtotal** | | **20 SP** | |

---

### Feature 2.5 — Admin Authentication
**Effort:** 14 SP

#### User Story 2.5.1
> **As an** admin,  
> **I want** secure login with JWT tokens and automatic session refresh,  
> **so that** I can access the dashboard without re-logging in frequently.

**Acceptance Criteria:**
- `POST /api/auth/login` with valid credentials → returns access token (15-min) + refresh token (7-day, httpOnly cookie)
- `POST /api/auth/refresh` with valid refresh cookie → returns new access token + rotates refresh token
- `POST /api/auth/logout` → invalidates refresh token
- Protected routes return `401` without valid access token
- Passwords stored as bcrypt hashes, never in plaintext

| Task | Description | SP | Complexity |
|---|---|---|---|
| T2.5.1.1 | Implement `POST /api/auth/login` with bcrypt verification | 3 | S |
| T2.5.1.2 | Implement JWT access token creation and signing | 2 | S |
| T2.5.1.3 | Implement refresh token: create, store hash in DB, set httpOnly cookie `[PARTIAL]` | 3 | S |
| T2.5.1.4 | Implement `POST /api/auth/refresh` with rotation (old token invalidated) `[PARTIAL]` | 3 | S |
| T2.5.1.5 | Implement `POST /api/auth/logout`: revoke refresh token `[PARTIAL]` | 1 | XS |
| T2.5.1.6 | Implement `get_current_admin` FastAPI dependency | 2 | S |
| T2.5.1.7 | Write `create_admin.py` script for initial admin user provisioning | 1 | XS |
| T2.5.1.8 | Normalize API router mounting to prevent duplicate `/api/*` path prefixing `[DONE]` | 1 | XS |
| **Subtotal** | | **15 SP** | |

---

### Feature 2.6 — WebSocket Endpoint Skeleton
**Effort:** 10 SP

#### User Story 2.6.1
> **As a** frontend engineer,  
> **I want** a WebSocket endpoint that accepts connections and handles the message protocol,  
> **so that** I can build and test the voice client before AI integration is complete.

| Task | Description | SP | Complexity |
|---|---|---|---|
| T2.6.1.1 | Implement `WS /ws/session/{session_id}` FastAPI WebSocket handler | 3 | S |
| T2.6.1.2 | Implement session token authentication on WebSocket connect | 2 | S |
| T2.6.1.3 | Implement connection registry: track active connections in Redis `[PENDING]` | 3 | S |
| T2.6.1.4 | Implement graceful disconnect handling and cleanup `[PARTIAL]` | 2 | S |
| **Subtotal** | | **10 SP** | |

---

## Epic 3 — AI Orchestration Engine ✅ Done (scaffolding)

**Goal:** A fully operational voice pipeline that conducts a complete survey interview with correct persona, state management, and prompt security.  
**Total Effort:** 97 SP (~5 weeks)  
**Completed:** April 2026

---

### Feature 3.1 — Persona Manager
**Effort:** 12 SP

#### User Story 3.1.1
> **As a** participant,  
> **I want** to interact with a named AI interviewer that has a consistent voice and accent throughout my session,  
> **so that** the experience feels coherent and professional.

| Task | Description | SP | Complexity |
|---|---|---|---|
| T3.1.1.1 | Define persona pool YAML configuration with 6+ personas (name, gender, accent, voice_id, greeting_style) | 2 | S |
| T3.1.1.2 | Implement `PersonaManager.assign_random()` — random selection from pool | 2 | S |
| T3.1.1.3 | Implement non-repetition logic: check last 3 sessions for same participant | 3 | S |
| T3.1.1.4 | Implement `Persona` dataclass and serialization to/from JSONB | 2 | S |
| T3.1.1.5 | Write unit tests: randomness distribution, non-repetition guarantee | 3 | S |
| **Subtotal** | | **12 SP** | |

---

### Feature 3.2 — Survey State Machine
**Effort:** 18 SP

#### User Story 3.2.1
> **As a** system architect,  
> **I want** a state machine that enforces strict forward-only question progression,  
> **so that** the AI cannot skip, revisit, or discuss out-of-scope questions.

**Acceptance Criteria:**
- State transitions are valid only according to defined transition table
- Invalid transitions raise `InvalidTransitionError` (logged as security events)
- State persisted to Redis on every transition
- On reconnect, state rehydrated from Redis (no data loss)

| Task | Description | SP | Complexity |
|---|---|---|---|
| T3.2.1.1 | Define state enum: `GREETING, ASKING, LISTENING, PROCESSING, LOGGING, CLOSING, COMPLETED, TERMINATED` | 1 | XS |
| T3.2.1.2 | Implement transition table as a dict of `{current_state: [valid_next_states]}` | 2 | S |
| T3.2.1.3 | Implement `SurveyStateMachine` class with `transition(new_state)` method | 3 | S |
| T3.2.1.4 | Implement `get_current_question()` — returns Question at `current_question_index` | 2 | S |
| T3.2.1.5 | Implement `advance()` — increment index, handle last question → CLOSING | 3 | S |
| T3.2.1.6 | Implement `skip_question(reason)` — log SKIPPED response, call `advance()` | 2 | S |
| T3.2.1.7 | Implement `terminate(reason)` — set TERMINATED state, log to DB | 2 | S |
| T3.2.1.8 | Implement Redis persistence: serialize/deserialize state on every transition | 3 | S |
| **Subtotal** | | **18 SP** | |

---

### Feature 3.3 — System Prompt Builder (Sandwiched Prompt)
**Effort:** 14 SP

#### User Story 3.3.1
> **As a** security engineer,  
> **I want** every AI call to use a sandwiched system prompt with immutable anchors,  
> **so that** no user input can override the AI's role, persona, or survey script.

**Acceptance Criteria:**
- Every generated prompt contains ANCHOR BLOCK A at the top
- Every generated prompt contains ANCHOR BLOCK B at the bottom
- Only `current_question` context is included (no other questions)
- Persona name, gender, and accent are injected correctly

| Task | Description | SP | Complexity |
|---|---|---|---|
| T3.3.1.1 | Write ANCHOR BLOCK A template (persona identity, 9 hard rules) | 3 | S |
| T3.3.1.2 | Write SURVEY CONTEXT template (title, participant, current question only) | 2 | S |
| T3.3.1.3 | Write ANCHOR BLOCK B template (repeat of hard rules) | 2 | S |
| T3.3.1.4 | Implement `PromptBuilder.build(persona, survey, question, participant)` — assembles full prompt | 3 | S |
| T3.3.1.5 | Write unit tests: verify both anchors present, verify no out-of-scope questions included | 2 | S |
| T3.3.1.6 | Implement refocus phrase template bank with 8+ phrase variants | 2 | S |
| **Subtotal** | | **14 SP** | |

---

### Feature 3.4 — OpenAI Realtime API Integration
**Effort:** 21 SP

#### User Story 3.4.1
> **As a** participant,  
> **I want** the AI to understand my spoken responses and reply in a natural voice without noticeable delay,  
> **so that** the interview feels like a real conversation.

**Acceptance Criteria:**
- End-to-end turn latency (speech end → AI audio start) < 3 seconds in normal conditions
- AI audio streams progressively (playback starts on first chunk)
- OpenAI API errors trigger graceful degradation (user-facing message, no crash)

| Task | Description | SP | Complexity |
|---|---|---|---|
| T3.4.1.1 | Implement `transcribe(audio_bytes)` using OpenAI Whisper API | 3 | S |
| T3.4.1.2 | Implement `generate_response(prompt, transcript)` using GPT-4o Chat API | 3 | S |
| T3.4.1.3 | Implement `synthesize_speech(text, voice_id)` using OpenAI TTS API with streaming | 5 | M |
| T3.4.1.4 | Implement OpenAI Realtime API WebSocket proxy (advanced mode) | 8 | L |
| T3.4.1.5 | Implement `run_turn(session, audio_bytes)` orchestration method | 3 | S |
| T3.4.1.6 | Implement exponential backoff for OpenAI rate limit errors | 2 | S |
| T3.4.1.7 | Implement fallback mode: Whisper + GPT-4o + TTS (non-realtime) | 3 | S |
| **Subtotal** | | **27 SP** | |

---

### Feature 3.5 — Response Logging & Session Completion
**Effort:** 10 SP

#### User Story 3.5.1
> **As an** admin,  
> **I want** every participant's response to be logged with the full transcript and metadata,  
> **so that** I can review the survey results after completion.

| Task | Description | SP | Complexity |
|---|---|---|---|
| T3.5.1.1 | Implement `ResponseLogger.log(session, question, transcript, metadata)` `[PARTIAL]` | 3 | S |
| T3.5.1.2 | Implement session completion: set status to COMPLETED, record `duration_seconds`, `completed_at` | 2 | S |
| T3.5.1.3 | Implement `CLOSING` state: AI delivers formal closing statement, then COMPLETED | 2 | S |
| T3.5.1.4 | Update participant `status` to COMPLETED on session completion | 1 | XS |
| T3.5.1.5 | Write integration test: full 3-question session → all responses logged → COMPLETED | 2 | S |
| T3.5.1.6 | Persist required `question_index` on websocket response insert `[DONE]` | 1 | XS |
| **Subtotal** | | **10 SP** | |

---

### Feature 3.6 — Voice Quality & Confidence Handling
**Effort:** 10 SP

#### User Story 3.6.1
> **As a** participant,  
> **I want** the AI to handle situations where it couldn't hear me clearly,  
> **so that** I don't feel confused if my answer wasn't captured.

| Task | Description | SP | Complexity |
|---|---|---|---|
| T3.6.1.1 | Implement confidence threshold check on Whisper output (< 0.7 → ask to repeat) | 3 | S |
| T3.6.1.2 | Implement audio energy check: too quiet → "Could you speak a little louder?" | 2 | S |
| T3.6.1.3 | Implement max re-asks limit (3 per question) → skip question after limit | 2 | S |
| T3.6.1.4 | Implement `refocus_count` tracking per question; after 3 refocuses → skip | 3 | S |
| **Subtotal** | | **10 SP** | |

---

## Epic 4 — Frontend Participant Experience ✅ Done (scaffolding)

**Goal:** A polished, accessible SPA that handles the complete voice session lifecycle.  
**Total Effort:** 76 SP (~5 weeks)  
**Completed:** April 2026

---

### Feature 4.1 — Survey Entry & Consent Flow
**Effort:** 12 SP

#### User Story 4.1.1
> **As a** participant,  
> **I want** to open my survey link and clearly understand what I'm about to do,  
> **so that** I can give informed consent before my voice is recorded.

| Task | Description | SP | Complexity |
|---|---|---|---|
| T4.1.1.1 | Implement `SurveyPage` route with session init API call on mount | 3 | S |
| T4.1.1.2 | Implement loading state, error states (invalid token, expired, already complete) | 3 | S |
| T4.1.1.3 | Implement consent modal with data usage notice and two actions (Agree / Decline) | 3 | S |
| T4.1.1.4 | Implement `PersonaCard` component: agent name, avatar, accent, greeting label | 2 | S |
| T4.1.1.5 | Store session state in Zustand `sessionStore` | 1 | XS |
| **Subtotal** | | **12 SP** | |

---

### Feature 4.2 — Core Voice Session Component
**Effort:** 26 SP

#### User Story 4.2.1
> **As a** participant,  
> **I want** to speak naturally and hear the AI's questions without pressing any buttons,  
> **so that** the interview feels like a real phone call.

| Task | Description | SP | Complexity |
|---|---|---|---|
| T4.2.1.1 | Implement `getUserMedia` microphone request with permission-denied error handling | 2 | S |
| T4.2.1.2 | Implement `AudioContext` + `AnalyserNode` setup in `VoiceSession.jsx` | 2 | S |
| T4.2.1.3 | Implement `useVAD.js` hook: RMS calculation, speech/silence event emission | 5 | M |
| T4.2.1.4 | Implement `MediaRecorder` start/stop tied to VAD events | 3 | S |
| T4.2.1.5 | Implement WebSocket client: connect, authenticate, send audio chunks | 5 | M |
| T4.2.1.6 | Implement TTS audio playback: receive chunks, decode, queue, play sequentially | 5 | M |
| T4.2.1.7 | Implement `AudioVisualizer.jsx`: waveform animation driven by `AnalyserNode` | 3 | S |
| T4.2.1.8 | Implement component lifecycle cleanup: close microphone, close WebSocket on unmount | 1 | XS |
| **Subtotal** | | **26 SP** | |

---

### Feature 4.3 — Session Progress & Status Display
**Effort:** 10 SP

#### User Story 4.3.1
> **As a** participant,  
> **I want** to see how far through the survey I am,  
> **so that** I know how much time is left and I stay engaged.

| Task | Description | SP | Complexity |
|---|---|---|---|
| T4.3.1.1 | Implement `QuestionProgress.jsx`: animated progress bar, "Q X of N" label | 2 | S |
| T4.3.1.2 | Advance progress bar on `question_advanced` WebSocket event | 2 | S |
| T4.3.1.3 | Implement "Listening..." / "Processing..." / "Speaking..." status text with animations | 3 | S |
| T4.3.1.4 | Implement `ConnectionStatus.jsx`: WebSocket connection state badge | 2 | S |
| T4.3.1.5 | Implement auto-reconnect with exponential backoff (max 5 attempts) | 1 | XS |
| **Subtotal** | | **10 SP** | |

---

### Feature 4.4 — Completion & Error Screens
**Effort:** 10 SP

#### User Story 4.4.1
> **As a** participant,  
> **I want** to receive a clear confirmation when my survey is complete,  
> **so that** I know my responses were captured.

| Task | Description | SP | Complexity |
|---|---|---|---|
| T4.4.1.1 | Implement `CompletionScreen.jsx`: personalized thank-you, session summary | 3 | S |
| T4.4.1.2 | Handle `session_terminated` WebSocket event: display neutral "session ended" message | 2 | S |
| T4.4.1.3 | Handle microphone not available: platform-specific instructions | 2 | S |
| T4.4.1.4 | Handle browser incompatibility detection (Safari MediaRecorder fallback) | 3 | S |
| **Subtotal** | | **10 SP** | |

---

### Feature 4.5 — Accessibility & Cross-Browser Compatibility
**Effort:** 10 SP

#### User Story 4.5.1
> **As a** participant with accessibility needs,  
> **I want** the survey page to be navigable by keyboard and compatible with screen readers,  
> **so that** I can participate regardless of how I access the web.

| Task | Description | SP | Complexity |
|---|---|---|---|
| T4.5.1.1 | Add `aria-live` regions for VAD status announcements | 2 | S |
| T4.5.1.2 | Verify all interactive elements are keyboard-accessible (tab order, focus rings) | 2 | S |
| T4.5.1.3 | Verify WCAG AA color contrast on all text elements | 1 | XS |
| T4.5.1.4 | Add visible audio playback pause button with accessible label | 2 | S |
| T4.5.1.5 | Test on Chrome (primary), Firefox, Safari, Chrome Android, Safari iOS | 3 | S |
| **Subtotal** | | **10 SP** | |

---

### Feature 4.6 — WebSocket Abstraction Service
**Effort:** 8 SP

#### User Story 4.6.1
> **As a** frontend engineer,  
> **I want** a clean WebSocket service abstraction,  
> **so that** voice session components don't contain low-level socket management code.

| Task | Description | SP | Complexity |
|---|---|---|---|
| T4.6.1.1 | Implement `websocketClient.js`: connect, send, receive, close, reconnect methods | 5 | M |
| T4.6.1.2 | Implement `useVoiceSession.js` custom hook wrapping websocketClient + audio lifecycle | 3 | S |
| **Subtotal** | | **8 SP** | |

---

## Epic 5 — Security Hardening ✅ Done (scaffolding)

**Goal:** All OWASP-relevant attack vectors mitigated. Adversarial testing passed. Prompt injection impossible.  
**Total Effort:** 68 SP (~4 weeks)  
**Completed:** April 2026

---

### Feature 5.1 — Input Sanitization Middleware
**Effort:** 18 SP

#### User Story 5.1.1
> **As a** security engineer,  
> **I want** all participant speech transcripts scanned for injection patterns before reaching the AI,  
> **so that** adversarial inputs cannot manipulate the AI's behavior.

**Acceptance Criteria:**
- 50+ known jailbreak inputs are blocked (verified by test suite)
- 20+ legitimate inputs are correctly allowed through
- Blocked inputs trigger a refocus response, not an error — session continues
- Every block event is logged with session ID, matched pattern, and timestamp

| Task | Description | SP | Complexity |
|---|---|---|---|
| T5.1.1.1 | Research and compile regex injection pattern library (15+ patterns) | 3 | S |
| T5.1.1.2 | Research and compile jailbreak keyword dictionary (50+ terms, loaded from file) | 3 | S |
| T5.1.1.3 | Implement `InputSanitizer.check(text)` → `SanitizationResult` | 5 | M |
| T5.1.1.4 | Implement length and character allowlist validation | 2 | S |
| T5.1.1.5 | Implement security event logging on BLOCK result | 2 | S |
| T5.1.1.6 | Write adversarial unit test suite: 50 jailbreak inputs → all BLOCK | 3 | S |
| **Subtotal** | | **18 SP** | |

---

### Feature 5.2 — OpenAI Moderation API Integration
**Effort:** 14 SP

#### User Story 5.2.1
> **As a** platform operator,  
> **I want** hate speech and harassment to trigger immediate session termination,  
> **so that** Voxora cannot be weaponized for abusive or harmful interactions.

| Task | Description | SP | Complexity |
|---|---|---|---|
| T5.2.1.1 | Implement `ModerationService.check(text)` → `ModerationResult` | 3 | S |
| T5.2.1.2 | Implement flagged-content session termination pipeline (DB → WebSocket close) | 5 | M |
| T5.2.1.3 | Implement retry logic for Moderation API failures (3 attempts + fail-open) | 2 | S |
| T5.2.1.4 | Write integration test: send hate speech → verify session TERMINATED + WS closed | 3 | S |
| T5.2.1.5 | Write integration test: verify legitimate input passes moderation | 1 | XS |
| **Subtotal** | | **14 SP** | |

---

### Feature 5.3 — Rate Limiting
**Effort:** 10 SP

#### User Story 5.3.1
> **As a** platform operator,  
> **I want** rate limits on all public endpoints,  
> **so that** the platform is protected from brute force and DoS attacks.

| Task | Description | SP | Complexity |
|---|---|---|---|
| T5.3.1.1 | Install and configure `slowapi` with Redis backend `[DONE]` | 2 | S |
| T5.3.1.2 | Apply rate limit to `POST /api/sessions/init` (10/min per IP) `[DONE]` | 1 | XS |
| T5.3.1.3 | Apply rate limit to `POST /api/auth/login` (5/min per IP) `[DONE]` | 1 | XS |
| T5.3.1.4 | Implement WebSocket connection counter per IP in Redis `[PENDING]` | 3 | S |
| T5.3.1.5 | Apply rate limit to admin endpoints (100/min per user) `[PARTIAL]` | 1 | XS |
| T5.3.1.6 | Write tests: verify 429 returned after threshold, `Retry-After` header present `[PARTIAL]` | 2 | S |
| **Subtotal** | | **10 SP** | |

---

### Feature 5.4 — JWT Security Hardening
**Effort:** 10 SP

#### User Story 5.4.1
> **As a** security engineer,  
> **I want** JWT handling to be resistant to known JWT attack vectors,  
> **so that** admin sessions cannot be hijacked or forged.

| Task | Description | SP | Complexity |
|---|---|---|---|
| T5.4.1.1 | Enforce `algorithm` field validation (reject `none` algorithm) | 2 | S |
| T5.4.1.2 | Validate `exp`, `sub`, and `iss` claims on every request | 2 | S |
| T5.4.1.3 | Implement refresh token rotation (old token invalidated on use) | 3 | S |
| T5.4.1.4 | Store refresh token hash in DB for revocation support | 2 | S |
| T5.4.1.5 | Test: algorithm confusion attack → 401; expired token → 401 | 1 | XS |
| **Subtotal** | | **10 SP** | |

---

### Feature 5.5 — Security Logging & Penetration Testing
**Effort:** 16 SP

#### User Story 5.5.1
> **As a** security engineer,  
> **I want** all security events captured in a structured, queryable log,  
> **so that** I can detect and investigate suspicious patterns.

| Task | Description | SP | Complexity |
|---|---|---|---|
| T5.5.1.1 | Define `SecurityEvent` structured log schema | 2 | S |
| T5.5.1.2 | Implement security event logging for: injection block, moderation flag, rate limit, invalid JWT | 3 | S |
| T5.5.1.3 | Configure separate log stream for security events | 2 | S |
| T5.5.1.4 | Conduct adversarial testing: unicode jailbreaks, multi-turn injection, base64 injection | 5 | M |
| T5.5.1.5 | Document findings and implement remediations | 3 | S |
| T5.5.1.6 | Configure CORS: restrict `ALLOWED_ORIGINS` to exact domain list | 1 | XS |
| **Subtotal** | | **16 SP** | |

---

## Epic 6 — Admin Dashboard ✅ Done (scaffolding)

**Goal:** Functional, secure admin dashboard with real-time analytics and participant management.  
**Total Effort:** 64 SP (~4 weeks)  
**Completed:** April 2026

---

### Feature 6.1 — Admin Analytics API
**Effort:** 16 SP

#### User Story 6.1.1
> **As an** admin,  
> **I want** real-time survey analytics,  
> **so that** I can track survey progress and identify drop-off patterns.

| Task | Description | SP | Complexity |
|---|---|---|---|
| T6.1.1.1 | Implement `GET /api/admin/stats`: participant counts by status, completion rate, avg duration, flag rate | 5 | M |
| T6.1.1.2 | Implement `GET /api/admin/participants` with pagination, status filter, name/email search | 5 | M |
| T6.1.1.3 | Implement `GET /api/admin/sessions/{id}` with full response transcript list | 3 | S |
| T6.1.1.4 | Implement `GET /api/admin/flagged`: flagged sessions with moderation details | 2 | S |
| T6.1.1.5 | Add Redis caching (30-second TTL) to stats endpoint | 1 | XS |
| **Subtotal** | | **16 SP** | |

---

### Feature 6.2 — Reminder System
**Effort:** 14 SP

#### User Story 6.2.1
> **As an** admin,  
> **I want** to send reminder emails to pending participants with a single click,  
> **so that** I can improve survey completion rates without manual effort.

| Task | Description | SP | Complexity |
|---|---|---|---|
| T6.2.1.1 | Implement `POST /api/admin/reminders`: validate participant IDs, check status is PENDING | 3 | S |
| T6.2.1.2 | Implement email sending via SMTP (SendGrid) with participant survey link | 5 | M |
| T6.2.1.3 | Update `participants.reminder_count` and `last_reminded_at` after send | 2 | S |
| T6.2.1.4 | Return send summary `{ sent, failed, details }` | 1 | XS |
| T6.2.1.5 | Write integration test: mock SMTP, verify reminder count increments | 3 | S |
| **Subtotal** | | **14 SP** | |

---

### Feature 6.3 — Admin Frontend — Login & Auth
**Effort:** 12 SP

#### User Story 6.3.1
> **As an** admin,  
> **I want** a secure login page with automatic token refresh,  
> **so that** I don't get logged out while actively using the dashboard.

| Task | Description | SP | Complexity |
|---|---|---|---|
| T6.3.1.1 | Implement `LoginPage.jsx` with username/password form and validation | 3 | S |
| T6.3.1.2 | Implement login API call, store access token in Zustand `adminStore` | 2 | S |
| T6.3.1.3 | Implement `ProtectedRoute` component: redirect to `/login` if not authenticated | 2 | S |
| T6.3.1.4 | Implement Axios interceptor: 401 → auto-refresh → retry original request | 3 | S |
| T6.3.1.5 | Implement page-refresh auth check: validate refresh cookie before logout | 2 | S |
| **Subtotal** | | **12 SP** | |

---

### Feature 6.4 — Admin Frontend — Dashboard Components
**Effort:** 22 SP

#### User Story 6.4.1
> **As an** admin,  
> **I want** a dashboard with charts, participant table, and reminder controls,  
> **so that** I can manage surveys without database access.

| Task | Description | SP | Complexity |
|---|---|---|---|
| T6.4.1.1 | Implement `StatsOverview.jsx`: KPI cards (total, pending, completed, flagged) | 3 | S |
| T6.4.1.2 | Implement completion rate donut chart using Recharts `PieChart` | 3 | S |
| T6.4.1.3 | Implement `ParticipantTable.jsx`: columns, status badges, pagination, filter, search | 5 | M |
| T6.4.1.4 | Implement `ReminderPanel.jsx`: checkbox select, custom message, send button | 5 | M |
| T6.4.1.5 | Implement `ResponseViewer.jsx`: per-question transcript display with metadata badges | 5 | M |
| T6.4.1.6 | Add auto-refresh polling (30-second interval) to stats and table | 1 | XS |
| **Subtotal** | | **22 SP** | |

---

## Epic 7 — Integration & Testing

**Goal:** Full test coverage across all integration points. No critical/high bugs remaining.  
**Total Effort:** 55 SP (~4 weeks)

---

### Feature 7.1 — Backend Integration Tests
**Effort:** 18 SP

| User Story | Description | Tasks | SP |
|---|---|---|---|
| 7.1.1 | Full session lifecycle test (init → voice turns → complete, mocked AI) | Write pytest: init, 3 turns, COMPLETED status, responses in DB | 5 |
| 7.1.2 | Sanitizer integration: injection input → blocked → session continues | Mock WebSocket, send injection payload, verify BLOCK + refocus sent | 3 |
| 7.1.3 | Moderation integration: hate speech → session TERMINATED → WS close | Mock moderation API, send flagged content, verify DB + WS close | 3 |
| 7.1.4 | Rate limiter integration with Redis | Send N+1 requests, verify 429 | 3 |
| 7.1.5 | Admin API: full survey CRUD + participant + reminder lifecycle | Write pytest for each endpoint | 4 |
| 7.1.6 | Focused auth/session contract regression suite | Add and run `test_auth_sessions_contracts.py` checks for routing, cookie refresh, response contracts, and rate limits `[DONE]` | 3 |
| **Subtotal** | | | **18 SP** |

---

### Feature 7.2 — Frontend E2E Tests
**Effort:** 16 SP

| User Story | Description | Tasks | SP |
|---|---|---|---|
| 7.2.1 | Participant: navigate to survey URL → consent → session init → voice session renders | Playwright test with WebSocket mock | 5 |
| 7.2.2 | Participant: simulate 3 audio turns → progress bar advances → completion screen | Playwright: inject audio chunks via WS mock | 5 |
| 7.2.3 | Admin: login → dashboard loads → filter participants → send reminder | Playwright: mock API responses | 3 |
| 7.2.4 | Error paths: invalid token → error screen; WS disconnect → reconnect attempt | Playwright: force WS close, verify reconnect UI | 3 |
| **Subtotal** | | | **16 SP** |

---

### Feature 7.3 — Load Testing
**Effort:** 12 SP

| User Story | Description | Tasks | SP |
|---|---|---|---|
| 7.3.1 | 50 concurrent voice sessions — WebSocket stability | Write k6/Locust scenario; run against staging | 5 |
| 7.3.2 | 200 concurrent REST requests — API latency validation (p95 < 200ms) | k6 ramp-up test on session init endpoint | 3 |
| 7.3.3 | Admin dashboard under load — no resource contention | k6 test admin stats endpoint under simulated session load | 2 |
| 7.3.4 | Document findings and implement remediations | Analysis report + index/connection pool adjustments | 2 |
| **Subtotal** | | | **12 SP** |

---

### Feature 7.4 — Security Regression Tests
**Effort:** 9 SP

| User Story | Description | Tasks | SP |
|---|---|---|---|
| 7.4.1 | Adversarial input test suite (50+ inputs) — all must BLOCK | Automated pytest run | 3 |
| 7.4.2 | JWT attack vectors — algorithm confusion, expired token, wrong session | Automated pytest | 3 |
| 7.4.3 | Sandwiched prompt verification — both anchors present in 100% of AI calls | Log-based verification test | 3 |
| **Subtotal** | | | **9 SP** |

---

## Epic 8 — DevOps & Deployment ✅ Done (scaffolding)

**Goal:** Production infrastructure with automated CI/CD, monitoring, and alerting.  
**Total Effort:** 52 SP (~4 weeks)  
**Completed:** April 2026

---

### Feature 8.1 — Production Docker & Nginx
**Effort:** 14 SP

| Task | Description | SP |
|---|---|---|
| T8.1.1 | Write production backend `Dockerfile`: multi-stage, non-root user, no dev deps | 3 |
| T8.1.2 | Write production frontend `Dockerfile`: build → Nginx static file server | 3 |
| T8.1.3 | Configure `nginx/default.conf`: TLS, HTTP→HTTPS redirect, HSTS, WebSocket proxy, gzip | 5 |
| T8.1.4 | Write `docker-compose.prod.yml` with resource limits and restart policies | 3 |
| **Subtotal** | | **14 SP** |

---

### Feature 8.2 — Cloud Infrastructure
**Effort:** 16 SP

| Task | Description | SP |
|---|---|---|
| T8.2.1 | Provision PostgreSQL with Multi-AZ, automated backups, correct parameter group | 5 |
| T8.2.2 | Provision Redis with AOF persistence | 2 |
| T8.2.3 | Provision application servers in VPC with private subnets for DB/Redis | 5 |
| T8.2.4 | Configure security groups: restrict DB/Redis access to backend only | 2 |
| T8.2.5 | Obtain and configure TLS certificates (Let's Encrypt or ACM) | 2 |
| **Subtotal** | | **16 SP** |

---

### Feature 8.3 — CI/CD Pipeline
**Effort:** 10 SP

| Task | Description | SP |
|---|---|---|
| T8.3.1 | Complete `deploy.yml`: build → push to container registry | 3 |
| T8.3.2 | Add migration step: `alembic upgrade head` as a CI job | 2 |
| T8.3.3 | Implement rolling deploy with health check gate | 3 |
| T8.3.4 | Configure staging environment (reduced resources, separate API key) | 2 |
| **Subtotal** | | **10 SP** |

---

### Feature 8.4 — Monitoring & Alerting
**Effort:** 12 SP

| Task | Description | SP |
|---|---|---|
| T8.4.1 | Configure `structlog` JSON logging in backend | 2 |
| T8.4.2 | Ship logs to aggregator (CloudWatch/Datadog) | 2 |
| T8.4.3 | Create dashboards: WS connections, turn latency, OpenAI errors, DB pool | 3 |
| T8.4.4 | Create alerts: WS error rate, turn latency, OpenAI failures, flag rate | 3 |
| T8.4.5 | Verify alerts fire correctly (manual trigger test) | 2 |
| **Subtotal** | | **12 SP** |

---

## Effort Summary by Role

| Role | Primary Epics | Est. Total SP | Est. Duration |
|---|---|---|---|
| Tech Lead | E1, E4 (review), E5 (review), E8 | ~100 SP | 28 weeks (part-time across all) |
| Backend Engineer | E2, E3 (partial), E7.1 | ~145 SP | 18–20 weeks |
| AI/ML Engineer | E3 (primary), E5.2 | ~110 SP | 16–18 weeks |
| Frontend Engineer | E4, E6.3, E6.4, E7.2 | ~115 SP | 15–18 weeks |
| QA Engineer | E7 (primary), regression testing | ~73 SP | 10–12 weeks |

---

## Sprint Allocation (2-Week Sprints)

| Sprint | Weeks | Focus |
|---|---|---|
| Sprint 1 | 1–2 | E1: Foundation, repo, Docker, scaffolding |
| Sprint 2 | 3–4 | E2: DB models, migrations, Survey/Question API |
| Sprint 3 | 5–6 | E2: Participant API, Session init, Auth |
| Sprint 4 | 7–8 | E3: Persona Manager, State Machine, Prompt Builder |
| Sprint 5 | 9–10 | E3: OpenAI integration (Whisper, GPT-4o, TTS) + E4: Routing, Consent flow |
| Sprint 6 | 11–12 | E3: Response logging, full E2E voice test + E4: VoiceSession component |
| Sprint 7 | 13–14 | E4: Progress, Completion, Accessibility + E5: Sanitizer |
| Sprint 8 | 15–16 | E5: Moderation, Rate limiting, JWT hardening + E6: Analytics API |
| Sprint 9 | 17–18 | E6: Reminder API, Admin frontend (Login, Stats, Table) + E7: Integration tests begin |
| Sprint 10 | 19–20 | E6: ResponseViewer, polish + E7: E2E tests, load testing |
| Sprint 11 | 21–22 | E7: Security regression + E8: Docker prod, Nginx, cloud infra |
| Sprint 12 | 23–24 | E8: CI/CD, monitoring, staging deploy + internal UAT |
| Sprint 13 | 25–26 | External beta, bug fixes, production hardening |
| Sprint 14 | 27–28 | Production launch, monitoring, handover documentation |

---

## Dependency Map

```
E1 (Foundation)
    │
    ├──► E2 (Backend API & DB) ──────────────────────────────┐
    │       │                                                │
    │       ├──► E3 (AI Orchestration) ──────────┐          │
    │       │       │                             │          │
    │       │       └──► E7.1 (Integration Tests)│          │
    │       │                                     │          │
    │       └──► E6.1 (Admin API) ───────┐        │          │
    │                                    │        │          │
    └──► E4 (Frontend) ─────────────────►│        │          │
             │                           │        │          │
             └──► E6.3/6.4 (Admin UI)◄──┘        │          │
                      │                           │          │
                      └──► E7.2 (E2E Tests) ◄────┘          │
                                                              │
E5 (Security) ────────────────────────────────────────────── ┘
    │ (runs in parallel with E3, E4, provides interfaces)
    │
    └──► E7.3/7.4 (Load + Security Tests)
                  │
                  └──► E8 (DevOps & Deployment)
                              │
                              └──► Launch
```
