# Voxora — Detailed Project Plan
## Phase-Wise Implementation Roadmap

> **Methodology:** Agile / Iterative — 2-week sprints  
> **Team Assumption:** 1 Tech Lead, 1 Backend Engineer, 1 Frontend Engineer, 1 AI/ML Engineer, 1 QA Engineer  
> **Total Estimated Duration:** 26–28 weeks (~7 months) from kickoff to production launch

---

## Plan Summary

| Phase | Name | Duration | Primary Output |
|---|---|---|---|
| 0 | Foundation & Environment Setup | Weeks 1–2 | Dev environment, repo, CI skeleton |
| 1 | Backend Core & Database | Weeks 3–6 | REST API, DB schema, auth, migrations |
| 2 | AI Orchestration Engine | Weeks 7–11 | Voice pipeline, state machine, personas |
| 3 | Frontend Participant Experience | Weeks 9–13 | SPA, voice UI, WebSocket client |
| 4 | Security Hardening | Weeks 12–15 | Sanitizer, moderation, prompt anchoring |
| 5 | Admin Dashboard | Weeks 14–17 | Analytics, participant management, reminders |
| 6 | Integration & End-to-End Testing | Weeks 18–21 | Full E2E test suite, load testing |
| 7 | Performance Optimization | Weeks 21–23 | Latency tuning, streaming, caching |
| 8 | Deployment & DevOps | Weeks 22–25 | Docker, Nginx, CI/CD, staging |
| 9 | UAT & Production Launch | Weeks 25–28 | Beta testing, go-live, handover |

> **Note:** Phases 2 and 3 overlap intentionally (parallel backend/frontend tracks).  
> Phase 4 overlaps with Phase 5 — security is hardened during dashboard development.

---

## Phase 0 — Foundation & Environment Setup
**Duration:** 2 weeks (Weeks 1–2)  
**Owner:** Tech Lead + All Engineers  
**Goal:** Establish a zero-ambiguity starting point. Every engineer should be able to clone the repo and have a fully working local environment within 30 minutes.

### Week 1 — Architecture Decisions & Infrastructure

**Day 1–2: Architecture Review**
- Finalize technology stack decisions (confirm FastAPI vs Express — **FastAPI selected**)
- Confirm AI provider (confirm OpenAI Realtime API as primary, ElevenLabs as optional TTS)
- Define WebSocket message protocol schema
- Define database entity relationship diagram
- Select deployment target (AWS, GCP, or Azure — document decision)

**Day 3–4: Repository & Project Skeleton**
- Initialize Git repository with branch protection rules (`main`, `develop`, `feature/*`)
- Create monorepo directory structure:
  ```
  /backend  — FastAPI Python application
  /frontend — React Vite application
  /nginx    — Reverse proxy configuration
  /.github  — CI/CD workflows
  ```
- Add `.gitignore`, `.editorconfig`, root `README.md` (placeholder)
- Configure pre-commit hooks (Black formatter, ESLint, trailing whitespace)

**Day 4–5: Docker Compose Local Environment**
- Write `docker-compose.yml` with services:
  - `postgres:16` — database with volume persistence
  - `redis:7-alpine` — session store
  - `backend` — FastAPI with hot reload
  - `frontend` — Vite dev server with hot reload
- Verify all services start and communicate on first `docker compose up`
- Write `docker-compose.prod.yml` skeleton (nginx + production builds)

### Week 2 — CI/CD & Code Quality Gates

**Day 6–7: Backend Scaffolding**
- Initialize Python virtual environment and `requirements.txt`
- Create FastAPI app factory (`main.py`) with health check endpoint (`GET /health`)
- Set up Pydantic `Settings` class for environment variable management
- Configure Alembic for database migrations
- Verify database connectivity with a test migration

**Day 8–9: Frontend Scaffolding**
- Initialize React + Vite project
- Install and configure Tailwind CSS with design tokens
- Set up React Router v6 with placeholder routes: `/`, `/survey/:participantId`, `/admin`, `/login`
- Configure Axios instance with base URL and interceptors
- Verify frontend dev server connects to backend health endpoint

**Day 10: CI Pipeline**
- Write GitHub Actions `ci.yml`:
  - Backend: `pytest` (unit tests), `ruff` (linter), `black --check` (formatter)
  - Frontend: `npm test`, `eslint`, `npm run build`
  - Trigger: every pull request to `develop` and `main`
- Confirm CI passes on an empty test suite

### Phase 0 Exit Criteria
- [ ] `docker compose up` produces a running environment with no errors
- [ ] `GET http://localhost:8000/health` returns `{"status": "ok"}`
- [ ] Frontend renders a placeholder page at `http://localhost:5173`
- [ ] GitHub Actions CI pipeline passes on an empty commit
- [ ] All engineers have verified their local setup independently

---

## Phase 1 — Backend Core & Database
**Duration:** 4 weeks (Weeks 3–6)  
**Owner:** Backend Engineer + Tech Lead  
**Goal:** Complete, tested, and documented REST API. All database tables created. Admin authentication working.

### Week 3 — Database Models & Migrations

**Database Schema Implementation**
- Implement SQLAlchemy ORM models:
  - `Survey` model (id, title, description, is_active, timestamps)
  - `Question` model (id, survey_id FK, order_index, question_text, question_type, expected_topics)
  - `Participant` model (id, survey_id FK, email, name, status enum, invite_token, reminder fields)
  - `Session` model (id, participant_id FK, persona JSONB, current_question_index, state enum, timestamps, flag fields)
  - `Response` model (id, session_id FK, question_id FK, transcript fields, sentiment, moderation fields)
  - `AdminUser` model (id, username, hashed_password, is_active)
- Write Alembic migration for initial schema
- Add database indexes:
  - `participants.invite_token` (unique index — used in every survey URL lookup)
  - `participants.status` (filter index — heavily queried by admin)
  - `sessions.participant_id` (FK index)
  - `responses.session_id` (FK index)
- Verify migration runs cleanly on fresh PostgreSQL instance
- Write database seed script for development data

**Pydantic Schemas**
- Create request/response schemas for all entities
- Add field validation (e.g., `status` must be a valid enum value)
- Add OpenAPI documentation strings to all schema fields

### Week 4 — Survey & Participant API Endpoints

**Survey Management API**
- `POST /api/surveys` — Create a new survey with questions
- `GET /api/surveys` — List all surveys (admin)
- `GET /api/surveys/{id}` — Get survey with questions
- `PUT /api/surveys/{id}` — Update survey
- `DELETE /api/surveys/{id}` — Soft delete (set `is_active = false`)
- `POST /api/surveys/{id}/questions` — Add question to survey
- `PUT /api/surveys/{id}/questions/{q_id}` — Update question

**Participant Management API**
- `POST /api/participants` — Bulk create participants for a survey (accepts list of emails/names)
- `GET /api/participants` — List with pagination and status filter
- `GET /api/participants/{id}` — Get participant detail
- Write invite token generation logic (UUID v4, cryptographically random)
- Write invite link formatter: `https://app.voxora.io/survey/{invite_token}`

### Week 5 — Session API & Admin Authentication

**Session Initialization API**
- `POST /api/sessions/init` — Core endpoint: validates invite token, creates session, assigns persona, returns session JWT
- `GET /api/sessions/{id}` — Returns current session state (for frontend reconnection)
- Implement persona assignment logic (random selection from configured pool)
- Implement session state persistence in Redis (session JWT → session state JSON)
- Handle edge cases:
  - Token already used and session COMPLETED → return completion message
  - Token already IN_PROGRESS → return existing session (reconnect flow)
  - Token not found → 404
  - Token EXPIRED → 410 Gone

**Admin Authentication**
- `POST /api/auth/login` — Validate username/password, return access + refresh tokens
- `POST /api/auth/refresh` — Exchange refresh token (httpOnly cookie) for new access token
- `POST /api/auth/logout` — Revoke refresh token
- Implement `bcrypt` password hashing for admin users
- Implement JWT creation and validation with `python-jose`
- Create `get_current_admin` dependency for protecting routes
- Write admin user creation script (`app/scripts/create_admin.py`)

### Week 6 — WebSocket Handler Skeleton & Integration Tests

**WebSocket Endpoint Skeleton**
- Implement `WS /ws/session/{session_id}` handler in FastAPI
- Handle connection lifecycle: accept → authenticate (session token) → register → disconnect
- Implement message routing based on `type` field
- Implement connection registry (track active connections per session in Redis)
- Return placeholder "echo" responses (AI integration comes in Phase 2)

**Integration Testing**
- Write pytest integration tests for:
  - Survey CRUD lifecycle
  - Participant creation and invite token generation
  - Session init (valid token, expired token, already completed)
  - Admin login/logout/refresh flow
  - WebSocket connect/disconnect
- Achieve 80%+ test coverage on API layer

### Phase 1 Exit Criteria
- [ ] All REST endpoints return correct HTTP status codes and response shapes
- [ ] Database migration runs cleanly from empty schema
- [ ] Admin login flow works end-to-end (login → JWT → protected route)
- [ ] Session init creates a session record and returns a session token
- [ ] WebSocket accepts and closes connections gracefully
- [ ] 80%+ test coverage on API routes
- [ ] API documentation auto-generated at `/docs` (Swagger UI)

---

## Phase 2 — AI Orchestration Engine
**Duration:** 5 weeks (Weeks 7–11)  
**Owner:** AI/ML Engineer + Backend Engineer  
**Goal:** A fully functional voice pipeline that conducts a complete survey interview end-to-end, with the state machine, system prompt, and AI calling working correctly.

### Week 7 — System Prompt Builder & Persona Manager

**Persona Manager (`persona_manager.py`)**
- Define persona pool configuration (JSON/YAML file):
  ```yaml
  personas:
    - name: "Aria"    gender: "female"   accent: "British RP"    voice_id: "..."
    - name: "Marcus"  gender: "male"     accent: "Neutral American" voice_id: "..."
    - name: "Priya"   gender: "female"   accent: "Indian English"  voice_id: "..."
    - name: "James"   gender: "male"     accent: "Australian"      voice_id: "..."
    - name: "Sofia"   gender: "female"   accent: "Neutral American" voice_id: "..."
    - name: "Chen"    gender: "neutral"  accent: "Neutral American" voice_id: "..."
  ```
- Implement `PersonaManager.assign_random()` → returns a `Persona` dataclass
- Ensure no two consecutive sessions for the same participant use the same persona
- Store assigned persona in `sessions.persona` JSONB column

**Voxora Interviewer System Prompt Builder (`voxora_interviewer.py`)**
- Implement `PromptBuilder.build(persona, survey, question, participant)` function
- Implement full sandwiched prompt structure:
  - ANCHOR BLOCK A (hard rules, persona identity, forbidden behaviors)
  - SURVEY CONTEXT (title, participant name, current question ONLY)
  - ANCHOR BLOCK B (repeat of hard rules — injection resistance)
- Implement `RefocusTemplateManager`:
  - Load refocus phrases from configurable template bank
  - `get_refocus_phrase(question_brief)` → returns randomly selected refocusing sentence
  - Track refocus count per question; after 3 → log SKIPPED and advance

**Unit Tests**
- Test that ANCHOR BLOCK A and B are always present in every generated prompt
- Test that only `current_question` context appears (no future/past questions)
- Test persona assignment randomness and non-repetition
- Test refocus phrase rotation

### Week 8 — State Machine Implementation

**Survey State Machine (`state_machine.py`)**
- Implement `SurveyStateMachine` class with states:
  ```
  GREETING → ASKING → LISTENING → PROCESSING → LOGGING → [next question or CLOSING] → COMPLETED
  ```
- Valid transitions defined in a transition table (reject invalid transitions)
- `get_current_question()` → returns `Question` object for current index only
- `advance()` → moves to next question or CLOSING if last question
- `skip_question(reason)` → logs as SKIPPED, calls `advance()`
- `terminate(reason)` → sets state to TERMINATED, logs reason
- State is persisted to Redis on every transition (survive backend restarts)
- Recovery: on WebSocket reconnect, state is rehydrated from Redis

**State Machine Unit Tests**
- Test each valid transition
- Test that invalid transitions raise `InvalidTransitionError`
- Test `advance()` correctly moves through all questions to COMPLETED
- Test state persistence and rehydration from Redis mock

### Week 9 — OpenAI Realtime API Integration

**AI Orchestrator (`ai_orchestrator.py`)**
- Implement `AIOrchestratorService` with:
  - `transcribe(audio_bytes)` → calls OpenAI Whisper API, returns transcript string
  - `generate_response(prompt, transcript, session_state)` → calls GPT-4o, returns text
  - `synthesize_speech(text, voice_id)` → calls OpenAI TTS or ElevenLabs, returns audio bytes
  - `run_turn(session, audio_bytes)` → orchestrates the full turn pipeline
- Implement OpenAI Realtime API client (WebSocket-to-WebSocket proxy):
  - Open connection to `wss://api.openai.com/v1/realtime`
  - Forward participant audio, relay AI audio response back
  - Handle OpenAI-side events: `input_audio_buffer.committed`, `response.audio.delta`, `response.done`
- Implement response streaming:
  - Stream TTS audio chunks back to participant WebSocket as they arrive
  - Do not wait for full response — start playback on first audio chunk

**Error Handling**
- OpenAI API timeout → send "I need a moment, please bear with me" audio response
- OpenAI rate limit → exponential backoff, queue request
- TTS failure → fall back to text response with notification to frontend

### Week 10 — End-to-End Voice Turn Integration

**WebSocket Handler — Full Integration**
- Replace placeholder echo with full orchestration pipeline:
  ```
  receive audio_chunk → buffer → on is_final → run_turn(session, audio_bytes)
  ```
- Integrate `InputSanitizer` (built in Phase 4 but interface defined now)
- Integrate `ModerationService` (built in Phase 4 but interface defined now)
- Integrate `StateMachine` for question advancement
- Emit correct WebSocket messages:
  - `ai_response_audio` with audio chunks and transcript
  - `question_advanced` when moving to next question
  - `session_completed` when all questions answered

**Full Session Flow Test (Manual)**
- Conduct a complete 5-question survey interview manually with real microphone
- Verify: greeting → Q1 → Q2 → ... → closing → COMPLETED status in DB
- Verify: persona name appears correctly throughout
- Verify: responses logged correctly in `responses` table

### Week 11 — STT/TTS Optimization & Fallback Modes

**Whisper Integration Hardening**
- Add language detection (flag unexpected languages as a security note)
- Add confidence threshold: if Whisper confidence < 0.7, ask participant to repeat
- Add audio quality check: if audio is too quiet/noisy, send "I didn't catch that" response

**TTS Voice Configuration**
- Map each persona `voice_id` to OpenAI TTS voice IDs: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`
- Configure ElevenLabs as an optional premium TTS provider (feature flag)
- Implement voice caching for frequently used phrases (greeting, thank-you, refocus phrases)

**Fallback Mode**
- If OpenAI Realtime API is unavailable, fall back to: Whisper STT → GPT-4o text → TTS pipeline
- Implement a `DEGRADED_MODE` flag that the frontend can detect and display a status indicator

### Phase 2 Exit Criteria
- [ ] Complete 5-question survey can be conducted end-to-end via voice (manual test)
- [ ] Persona is correctly named and maintains identity throughout the session
- [ ] State machine correctly advances through all questions to COMPLETED
- [ ] All responses logged to database with transcripts
- [ ] System prompt contains both ANCHOR blocks in every AI call (verified via logging)
- [ ] TTS audio streams back to browser and plays correctly
- [ ] Refocusing triggers after 3 consecutive off-topic attempts

---

## Phase 3 — Frontend Participant Experience
**Duration:** 5 weeks (Weeks 9–13, overlaps with Phase 2)  
**Owner:** Frontend Engineer + Tech Lead  
**Goal:** A polished, accessible, and fully functional participant-facing SPA that handles the complete voice session lifecycle.

### Week 9–10 — Routing, Session Init & Persona Display

**Routing Setup**
- Configure React Router routes:
  - `/survey/:participantId` → `SurveyPage`
  - `/admin` → `AdminPage` (protected)
  - `/login` → `LoginPage`
  - `*` → `NotFoundPage`
- Implement `ProtectedRoute` component for admin (checks JWT in Zustand store)

**Session Initialization Flow (`SurveyPage.jsx`)**
- On mount: call `POST /api/sessions/init` with `participantId`
- Handle states: loading spinner → error (invalid token) → session ready
- Store session data in Zustand `sessionStore`: session ID, persona, question count, session token
- Display `PersonaCard` component: persona name, avatar placeholder, accent label

**Consent Screen**
- Before microphone access: display a consent modal explaining:
  - Voice will be recorded and transcribed
  - Data usage policy
  - How to withdraw
- "I Agree" button → proceed to microphone permission request
- "Decline" → friendly exit message, no session created

### Week 11 — Core Voice Session Component

**VoiceSession Component (`VoiceSession.jsx`)**
- Request microphone access: `navigator.mediaDevices.getUserMedia({ audio: true })`
- Handle permission denied gracefully (display instructions for browser settings)
- Initialize `AudioContext` and `AnalyserNode`
- Connect microphone stream to VAD processor
- Open WebSocket connection to `WSS /ws/session/{sessionId}`
- Authenticate WebSocket with session token (send token in first message)
- Manage component lifecycle: mount → connect → active → complete/error → unmount cleanup

**VAD Hook (`useVAD.js`)**
- `AnalyserNode` polling at 50ms intervals
- Compute RMS energy from `getFloatTimeDomainData()`
- Emit `onSpeechStart` event when RMS > threshold
- Emit `onSpeechEnd` event after silence for 800ms
- Expose `isSpeaking` state for visualizer

**Audio Capture & Streaming**
- On `onSpeechStart`: initialize `MediaRecorder` with `audio/webm;codecs=opus`
- Collect `dataavailable` chunks in buffer
- On `onSpeechEnd`: stop recorder, send final chunk over WebSocket with `is_final: true`

**Audio Playback**
- Receive `ai_response_audio` messages from WebSocket
- Decode base64 audio data
- Use `AudioContext.decodeAudioData()` → `AudioBufferSourceNode.start()`
- Implement audio queue: if AI response arrives while still playing, queue for sequential playback

**Connection Status (`ConnectionStatus.jsx`)**
- Display WebSocket status badge: Connecting / Connected / Reconnecting / Error
- Auto-reconnect with exponential backoff (max 5 attempts)
- On max reconnect failure: display "Connection lost" with a "Try Again" button

### Week 12 — Progress Tracking & Question Display

**QuestionProgress Component**
- Display "Question X of N" progress bar
- Animate progress bar advancement on `question_advanced` WebSocket event
- Display current question text (for accessibility — visual text alongside audio)

**Audio Visualizer (`AudioVisualizer.jsx`)**
- Animate a waveform/pulsing circle using `AnalyserNode` frequency data
- Two states: participant speaking (warm color) vs. AI speaking (cool color)
- Idle state: gentle ambient pulse

**State Feedback**
- Display "Listening..." text with animated dots when VAD detects speech
- Display "Processing..." overlay briefly between participant speech end and AI response start
- Display "Speaking..." indicator while AI audio plays (prevent premature re-recording)

### Week 13 — Completion Screen, Error Handling & Accessibility

**CompletionScreen Component**
- Display on receipt of `session_completed` WebSocket message
- Show personalized thank-you message with participant first name
- Display session summary: total questions, duration
- Optional: display a static "feedback received" confirmation graphic

**Error States**
- Handle `session_terminated` (content policy): display neutral "This session has ended" message — no reason shown to participant
- Handle invalid/expired invite token: display "This link is no longer valid" with a support contact
- Handle microphone not available: device-specific instructions
- Handle browser incompatibility (Safari WebRTC limitations): display alternative instructions

**Accessibility**
- All interactive elements keyboard-navigable
- `aria-live` regions for status announcements (for screen readers)
- Sufficient color contrast (WCAG AA minimum)
- Audio control: visible "pause" button to pause AI playback

**Cross-Browser Testing**
- Chrome (primary target)
- Firefox
- Safari (WebRTC + MediaRecorder differences)
- Mobile: Chrome on Android, Safari on iOS

### Phase 3 Exit Criteria
- [ ] Participant can navigate to `/survey/:id`, consent, and enter a voice session
- [ ] Microphone capture, VAD, and audio sending work correctly in Chrome and Firefox
- [ ] AI audio plays back correctly with correct sequential ordering
- [ ] Progress bar advances correctly after each question
- [ ] Completion screen displays on session end
- [ ] Session terminated message displays without leaking reason details
- [ ] Accessible: keyboard navigation and screen reader tested

---

## Phase 4 — Security Hardening
**Duration:** 4 weeks (Weeks 12–15, overlaps with Phases 3 & 5)  
**Owner:** Tech Lead + Backend Engineer  
**Goal:** All security layers are implemented, tested with adversarial inputs, and documented. No single layer failure should compromise the session.

### Week 12 — Input Sanitizer Implementation

**InputSanitizer (`input_sanitizer.py`)**
- Build pattern library (regex-based):
  ```python
  INJECTION_PATTERNS = [
      r"ignore\s+(all\s+)?previous\s+instructions?",
      r"forget\s+your\s+(instructions?|role|prompt|rules?)",
      r"you\s+are\s+now\s+",
      r"pretend\s+to\s+be",
      r"act\s+as\s+(if\s+you\s+(were|are)\s+)?(?!a\s+participant)",
      r"\bDAN\b",
      r"developer\s+mode",
      r"jailbreak",
      r"sudo\s+mode",
      r"override\s+(your\s+)?(instructions?|rules?|role)",
      r"reveal\s+(your\s+)?(prompt|instructions?|system\s+prompt)",
      r"bypass\s+(your\s+)?(safety|filter|rules?)",
      r"ignore\s+(your\s+)?(guidelines?|rules?|instructions?)",
      r"what\s+(are|were)\s+your\s+(instructions?|orders?)",
  ]
  ```
- Build jailbreak keyword dictionary (curated list, loaded from configurable file)
- Implement length validation: reject inputs > 2000 characters
- Implement character allowlist: reject control characters and non-printable unicode
- `SanitizationResult` dataclass: `{ is_safe: bool, matched_pattern: str | None, action: "PASS" | "BLOCK" | "WARN" }`
- On BLOCK: log security event with timestamp, session ID, matched pattern, raw input; return refocus response

**Unit Tests — Adversarial Input Suite**
- Test 50+ known jailbreak inputs (must all BLOCK)
- Test 20 legitimate participant responses (must all PASS)
- Test edge cases: partial matches, leetspeak variations, unicode substitutions

### Week 13 — OpenAI Moderation API Integration

**ModerationService (`moderation.py`)**
- Implement `ModerationService.check(text)` → calls `POST https://api.openai.com/v1/moderations`
- Parse response categories: `hate`, `hate/threatening`, `harassment`, `self-harm`, `sexual`, `violence`
- `ModerationResult` dataclass: `{ is_flagged: bool, categories: dict, flagged_categories: list[str] }`
- On flagged:
  1. Log to `responses.moderation_flagged = True`, store `moderation_categories` JSONB
  2. Set `sessions.is_flagged = True`, `sessions.flag_reason = flagged_categories[0]`
  3. Call `StateMachine.terminate("content_policy_violation")`
  4. Send `session_terminated` WebSocket message
  5. Close WebSocket with code `1008`
- Implement retry logic (3 attempts with 1s backoff) for Moderation API failures
- On Moderation API unavailability: fail open with a WARNING log (do not block legitimate sessions)

**Integration with WebSocket Handler**
- Moderation check runs AFTER sanitizer PASS, BEFORE AI orchestration
- Total middleware pipeline: `sanitizer → moderator → orchestrator`
- Add timing metrics: log duration of each middleware stage

### Week 14 — Rate Limiting & JWT Hardening

**Rate Limiter (`rate_limiter.py`)**
- Install and configure `slowapi` with Redis backend
- Rules:
  - `POST /api/sessions/init`: 10 requests/minute per IP
  - `POST /api/auth/login`: 5 requests/minute per IP (brute force protection)
  - `WS /ws/session/*`: 5 concurrent connections per IP
  - Admin endpoints: 100 requests/minute per authenticated user
- On limit exceeded: return `429 Too Many Requests` with `Retry-After` header
- Log rate limit violations as security events

**JWT Hardening**
- Verify `algorithm` field matches expected `HS256` (prevent algorithm confusion attacks)
- Validate `exp` claim on every request
- Validate `sub` claim against admin users table on every admin request
- Implement refresh token rotation (each use of refresh token invalidates old one, issues new)
- Store refresh token hash in database (not the token itself) for revocation support

**CORS Hardening**
- Restrict `ALLOWED_ORIGINS` to exact domain list (no wildcards in production)
- Set `allow_credentials=True` only for admin routes

### Week 15 — Penetration Testing & Security Documentation

**Adversarial Testing Session**
- Attempt to bypass sanitizer with:
  - Unicode lookalike characters (е vs e)
  - Zero-width characters inserted in injection phrases
  - Base64 encoded injection commands
  - Multi-turn injection (spread injection across multiple messages)
  - Prompt injection via "my name is [injection payload]"
- Attempt to bypass JWT:
  - Algorithm confusion (none algorithm)
  - Expired token replay
  - Token from different session
- Attempt rate limit bypass via IP rotation (document finding, recommend Cloudflare WAF)
- Document all findings and remediations

**Security Logging**
- Implement structured security event logging:
  ```python
  SecurityEvent(
      event_type="INJECTION_ATTEMPT" | "MODERATION_FLAG" | "RATE_LIMIT" | "INVALID_STATE_TRANSITION",
      session_id=..., ip_address=..., details={...}, timestamp=...
  )
  ```
- Security events written to dedicated log stream (separate from application logs)

### Phase 4 Exit Criteria
- [ ] 50+ jailbreak inputs are blocked by sanitizer (verified by unit tests)
- [ ] Moderation API integration terminates sessions on hate/harassment content
- [ ] Rate limiter returns 429 correctly after threshold exceeded
- [ ] JWT algorithm confusion attack is rejected
- [ ] Refresh token rotation implemented and tested
- [ ] Sandwiched prompt: both ANCHOR blocks present in 100% of AI calls (verified by test)
- [ ] Security event log captures all violation types

---

## Phase 5 — Admin Dashboard
**Duration:** 4 weeks (Weeks 14–17)  
**Owner:** Frontend Engineer + Backend Engineer  
**Goal:** A fully functional, secure admin dashboard with real-time analytics and participant management.

### Week 14–15 — Admin API Completion

**Analytics API**
- `GET /api/admin/stats` → KPI summary:
  - Total participants, by status breakdown
  - Completion rate %
  - Average session duration
  - Flag rate %
  - Average refocus rate
- `GET /api/admin/participants?status=&page=&per_page=&search=` → paginated list
- `GET /api/admin/sessions/{id}` → session detail with all responses and transcripts
- `GET /api/admin/flagged` → flagged sessions with moderation categories
- `GET /api/admin/surveys/{id}/analytics` → per-survey breakdown

**Reminder API**
- `POST /api/admin/reminders` → body: `{ participant_ids: [uuid, ...], message: string }`
- Send emails via SMTP (SendGrid or AWS SES)
- Update `participants.reminder_count` and `last_reminded_at`
- Return: `{ sent: N, failed: M, details: [...] }`

### Week 15–16 — Admin Frontend Components

**Login Page (`LoginPage.jsx`)**
- Username/password form with validation
- Submit → `POST /api/auth/login` → store access token in Zustand `adminStore`
- Store refresh token as httpOnly cookie (handled by browser)
- Redirect to `/admin` on success

**Stats Overview (`StatsOverview.jsx`)**
- KPI cards: Total / Pending / In Progress / Completed / Flagged counts
- Completion rate donut chart (Recharts `PieChart`)
- Session duration histogram (Recharts `BarChart`)
- Auto-refresh every 30 seconds (polling or WebSocket updates)

**Participant Table (`ParticipantTable.jsx`)**
- Columns: Name, Email, Status (color-coded badge), Invite Sent, Reminder Count, Actions
- Server-side pagination (10/25/50 per page)
- Filter by status (dropdown)
- Search by name or email
- Row actions: View Session, Send Reminder, Manually mark status

**Reminder Panel (`ReminderPanel.jsx`)**
- Checkbox-select participants with `PENDING` status
- Custom message text area with character count
- "Send Reminder" button → calls `POST /api/admin/reminders`
- Display success/failure summary after sending

**Response Viewer (`ResponseViewer.jsx`)**
- Per-session view: persona used, duration, completion status
- Per-question transcript display:
  - Question text (left column)
  - Participant transcript (right column)
  - Sentiment indicator if available
  - Refocus count badge
  - Moderation flag indicator
- Copy transcript button

### Week 17 — Admin Polish & Protected Routes

**JWT Interceptor (Frontend)**
- Axios interceptor: on 401 response, attempt token refresh via `POST /api/auth/refresh`
- On refresh success: retry original request
- On refresh failure: clear auth state, redirect to `/login`

**Admin Route Protection**
- `ProtectedRoute` component: check Zustand auth state → redirect to `/login` if not authenticated
- On page refresh: check for valid refresh cookie before logging out

**Admin UI Polish**
- Responsive layout (desktop and tablet)
- Loading skeletons for data tables
- Empty states for tables with zero data
- Toast notifications for actions (reminder sent, status updated)
- Confirm dialog for destructive actions

### Phase 5 Exit Criteria
- [ ] Admin can log in and see the dashboard
- [ ] KPIs load and reflect actual database data
- [ ] Participant table filters and pagination work correctly
- [ ] Reminders can be sent and reminder count updates in DB
- [ ] Session detail shows full transcript per question
- [ ] JWT refresh flow works (auto-retry on 401)
- [ ] Admin routes return 401 without valid token

---

## Phase 6 — Integration & End-to-End Testing
**Duration:** 4 weeks (Weeks 18–21)  
**Owner:** QA Engineer + All Engineers  
**Goal:** Full test coverage across all integration points. No critical or high-severity bugs remaining.

### Week 18–19 — Integration Test Suite

**Backend Integration Tests**
- Full session lifecycle: init → voice turns → complete (using mocked OpenAI)
- Sanitizer integration: injected input → blocked → refocus sent → session continues
- Moderation integration: flagged content → session terminated → WebSocket closed
- State machine: all questions answered → COMPLETED status → duration logged
- Admin API: CRUD operations on surveys, participants, and sessions
- Rate limiter: verify 429 after threshold with Redis integration

**Frontend Integration Tests**
- Playwright or Cypress E2E tests:
  - Navigate to survey URL → consent → voice session page loads
  - Simulate audio chunks via WebSocket mock → AI response plays → progress advances
  - Complete all questions → completion screen renders
  - Admin login → dashboard loads → reminder sent
  - Invalid token → 404/error page

**Security Integration Tests**
- Send injection payload via WebSocket → verify it is blocked, session continues
- Send hate speech content → verify session termination → WebSocket close code 1008
- Attempt admin endpoint without token → 401
- Attempt expired JWT → 401

### Week 20–21 — Load Testing & Performance Validation

**Load Testing (Locust or k6)**
- Scenario 1: 50 concurrent voice sessions — measure WebSocket stability
- Scenario 2: 200 concurrent REST API requests — measure API latency (p95 < 200ms)
- Scenario 3: Rapid session init (simulate invitation email blast) — measure DB bottleneck
- Scenario 4: Admin dashboard polling under load — verify no resource contention

**Performance Benchmarks**
- Target: End-to-end turn latency (speech end → AI audio starts) < 3 seconds
- Target: Session init API response < 500ms at p95
- Target: Admin stats API response < 1 second at p95

### Phase 6 Exit Criteria
- [ ] All integration tests pass
- [ ] E2E tests: participant voice session completes successfully
- [ ] Security tests: injection and moderation scenarios behave as designed
- [ ] Load test: 50 concurrent sessions stable for 10 minutes with no errors
- [ ] p95 turn latency < 3 seconds on staging environment
- [ ] Zero open critical or high-severity bugs

---

## Phase 7 — Performance Optimization
**Duration:** 3 weeks (Weeks 21–23)  
**Owner:** Tech Lead + AI Engineer  
**Goal:** Minimize voice turn latency and optimize resource usage for cost efficiency.

### Week 21 — Audio Pipeline Optimization

- Reduce VAD silence threshold from 800ms to 600ms (tune based on testing)
- Implement audio pre-roll buffer: send first 200ms of speech earlier to reduce perceived latency
- Enable TTS audio streaming: start sending audio to client on first 500-byte chunk (vs waiting for full response)
- Cache frequently used audio phrases (greeting, refocus phrases) in Redis as pre-synthesized audio bytes
- Measure: before vs. after latency for 20 real voice turns

### Week 22 — Database & API Optimization

- Add `EXPLAIN ANALYZE` to all slow queries identified in load testing
- Add composite indexes identified during load test analysis
- Implement SQLAlchemy connection pooling: `pool_size=10, max_overflow=20`
- Add Redis caching for admin stats endpoint (cache 30 seconds)
- Paginate all list endpoints (enforce `max_page_size=100`)

### Week 23 — Cost & Resource Optimization

- Analyze OpenAI API usage (tokens, TTS characters) per session
- Optimize system prompt length (every token costs money): remove redundant language while preserving security
- Implement audio compression for participant uploads (ensure Opus codec is used)
- Set WebSocket idle timeout (disconnect sessions inactive for > 5 minutes)
- Implement session cleanup job: archive COMPLETED sessions audio after 30 days

### Phase 7 Exit Criteria
- [ ] End-to-end turn latency reduced by measurable percentage from Phase 6 baseline
- [ ] Cached phrases reduce TTS API calls by estimated 20%+
- [ ] Database query p95 < 50ms for all common queries
- [ ] OpenAI token cost per session estimated and documented

---

## Phase 8 — Deployment & DevOps
**Duration:** 4 weeks (Weeks 22–25)  
**Owner:** Tech Lead + Backend Engineer  
**Goal:** Production-ready infrastructure with automated deployment pipeline.

### Week 22 — Docker & Nginx Production Configuration

- Write production `Dockerfile` for backend (multi-stage, non-root user)
- Write production `Dockerfile` for frontend (build → Nginx static file server)
- Configure Nginx:
  - TLS termination with Let's Encrypt certificates
  - HTTP → HTTPS redirect
  - HSTS header (`max-age=31536000; includeSubDomains`)
  - WebSocket proxy with appropriate timeout settings
  - Gzip compression for API responses
  - Static asset caching headers for frontend
- Write `docker-compose.prod.yml` with:
  - Production images (no volume mounts, no hot reload)
  - Health checks for all services
  - Resource limits (`mem_limit`, `cpus`)
  - Restart policies (`restart: always`)

### Week 23 — Cloud Infrastructure Setup

- Provision PostgreSQL (RDS / Cloud SQL):
  - Multi-AZ for high availability
  - Automated daily backups with 30-day retention
  - Parameter group: `max_connections=200`, `work_mem=16MB`
- Provision Redis (ElastiCache / Memorystore):
  - Single-node (Redis Cluster optional for high scale)
  - Enable AOF persistence
- Provision application servers (EC2 / Cloud Run / App Service)
- Configure VPC: database and Redis in private subnet, no public access
- Configure security groups: allow backend → DB on port 5432 only; backend → Redis on 6379 only

### Week 24 — CI/CD Pipeline Completion

**GitHub Actions `deploy.yml`**
- Trigger: merge to `main`
- Steps:
  1. Run full test suite
  2. Build Docker images
  3. Push to container registry (ECR / GCR / ACR)
  4. Run `alembic upgrade head` on production database (via migration job)
  5. Rolling deploy to application servers (no downtime)
  6. Health check: wait for `GET /health` to return 200
  7. Slack/Teams notification on success or failure

**Staging Environment**
- Mirror of production with reduced resources
- Connected to staging OpenAI API key with spending limit
- Used for QA sign-off before every production deployment

### Week 25 — Monitoring & Alerting

- Configure structured JSON logging (backend uses `structlog`)
- Ship logs to aggregator (CloudWatch / Datadog / Grafana Loki)
- Create dashboards:
  - Active WebSocket connections over time
  - Turn latency p50/p95/p99
  - OpenAI API error rates
  - Database connection pool utilization
  - Security events timeline
- Create alerts:
  - WebSocket error rate > 5% → PagerDuty/Slack alert
  - Turn latency p95 > 5 seconds → alert
  - OpenAI API failures > 10/min → alert
  - Flagged session rate > 2% → alert

### Phase 8 Exit Criteria
- [ ] Production Docker images build and deploy without errors
- [ ] Staging environment is a functional mirror of production
- [ ] `alembic upgrade head` runs in CI without manual intervention
- [ ] Nginx serves HTTPS with A-grade SSL Labs score
- [ ] All alerts configured and tested (triggered manually, notifications received)
- [ ] Database backup verified by restoration test

---

## Phase 9 — UAT & Production Launch
**Duration:** 4 weeks (Weeks 25–28)  
**Owner:** Tech Lead + Product Owner + All Engineers  
**Goal:** Successful production launch with real participants, stable operation, and a documented handover.

### Week 25–26 — User Acceptance Testing (UAT)

**Internal Beta (Week 25)**
- Invite 10 internal users to complete a 5-question test survey
- Collect feedback on:
  - Voice quality and clarity
  - AI persona naturalness
  - Session flow smoothness
  - Any bugs or confusion points
- Fix all UAT-identified issues before external beta

**External Beta (Week 26)**
- Invite 25–50 real target participants
- Monitor in real-time: active sessions dashboard, error logs, latency metrics
- Conduct a debrief interview with 5 participants on experience quality
- Identify and triage any new issues

### Week 27 — Production Hardening & Final Fixes

- Fix all issues from external beta
- Conduct final security review (check all Phase 4 items still hold)
- Final load test on production infrastructure (50 concurrent sessions)
- Verify backup/restore procedure one final time
- Verify all monitoring dashboards and alerts are live

### Week 28 — Production Launch & Handover

**Launch Checklist**
- [ ] All production environment variables set correctly
- [ ] Admin user credentials provisioned and distributed securely
- [ ] Participant invite batch loaded and links generated
- [ ] SMTP/email service verified (send a test reminder)
- [ ] OpenAI API spending limits set
- [ ] DNS records verified and propagated
- [ ] Launch announcement sent to stakeholders

**Handover Documentation**
- Runbook: How to create a new survey and load participants
- Runbook: How to monitor active sessions and respond to alerts
- Runbook: How to handle a flagged session report
- Runbook: How to deploy a new version
- Architecture decision records (ADRs) for key decisions made during development

### Phase 9 Exit Criteria
- [ ] 10+ successful end-to-end sessions completed with real users in production
- [ ] No critical bugs open
- [ ] Operations team can deploy, monitor, and respond to alerts independently
- [ ] All runbooks written and reviewed

---

## Risk Register & Contingency Plans

| Risk | Probability | Impact | Contingency |
|---|---|---|---|
| OpenAI Realtime API latency is too high for good UX | Medium | High | Fall back to Whisper → GPT-4o → TTS pipeline; add "processing" animation to mask latency |
| OpenAI Realtime API pricing makes production unviable | Low | Critical | Implement ElevenLabs TTS + Whisper + OpenAI Chat (non-realtime) as primary pipeline |
| Safari WebRTC/MediaRecorder incompatibility | High | Medium | Detect Safari, serve a polyfill or display instructions to use Chrome/Firefox |
| PostgreSQL performance bottleneck under load | Medium | High | Add PgBouncer connection pooler; scale DB vertically; offload reads to read replica |
| Jailbreak techniques evolve beyond current blocklist | Medium | Medium | Sandwiched prompt + moderation API provide defense-in-depth; schedule monthly blocklist reviews |
| Phase 2 AI integration delays Phase 3 frontend | Medium | Medium | Frontend can develop with WebSocket mock server; teams work in parallel with agreed API contracts |
| Team member unavailability | Low | Medium | Cross-train backend and frontend engineers on each other's modules from Week 1 |

---

## Definition of Done

A feature is "Done" when:
1. Code is written and reviewed (PR approved by at least 1 other engineer)
2. Unit tests written and passing (80%+ coverage on new code)
3. Integration test covering the feature exists and passes
4. API documentation updated (if applicable)
5. No new lint errors or type errors introduced
6. Deployed to staging environment and manually verified
7. QA engineer sign-off obtained
