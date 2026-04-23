# VoxOra — Issue Tracker
> **Source:** [IMPLEMENTATION_GAP_ANALYSIS.md](IMPLEMENTATION_GAP_ANALYSIS.md)  
> **Created:** April 23, 2026  
> **Tracking:** 30 issues across 4 categories — Critical Bugs, Security, Feature Gaps, Doc/Code Quality

---

## Status Legend

| Badge | Meaning |
|---|---|
| 🔴 Open | Not started |
| 🟡 In Progress | Work has begun |
| 🟢 Done | Merged / Resolved |
| ⚫ Blocked | Waiting on dependency |

---

## Milestone Overview

| Milestone | Label | Issues | Goal |
|---|---|---|---|
| M1 — Bootable | `critical` | IS-01 → IS-06 | App starts and handles one real request end-to-end |
| M2 — Secure | `security` | IS-07 → IS-09 | All documented security layers are active |
| M3 — Database | `infrastructure` | IS-10 | Reproducible DB creation via Alembic |
| M4 — Correct | `feature` | IS-11 → IS-19 | All documented P1/P2 features are present |
| M5 — Quality | `testing` `devops` `enhancement` | IS-20 → IS-30 | Tests, CI, and doc consistency |

---

## M1 — Critical Bugs (must fix before any integration test)

---

### IS-01 🔴 Fix `Session` model `started_at` / `created_at` field name mismatch

**Gap ref:** BUG-01  
**Labels:** `bug` `critical` `backend`  
**Milestone:** M1 — Bootable

#### User Story
> **As a** developer running the application,  
> **I want** all references to the Session timestamp column to use the correct field name,  
> **so that** the admin flagged-sessions endpoint and the session state endpoint do not crash with `AttributeError`.

#### Context
`Session` ORM model defines `started_at`. Two endpoints reference the non-existent `session.created_at`:
- `admin.py:99` — `.order_by(VoiceSession.created_at.desc())`
- `sessions.py:126` — `created_at=session.created_at`

`SessionStateResponse` schema declares `started_at: datetime`, but the endpoint keyword argument is `created_at=...`.

#### Acceptance Criteria
- [ ] `GET /api/admin/flagged` returns paginated results without `AttributeError`
- [ ] `GET /api/sessions/{id}` returns `SessionStateResponse` without `AttributeError`
- [ ] `Session.started_at` is the single source of truth for the session creation timestamp
- [ ] `SessionStateResponse` schema field name matches the endpoint keyword argument

#### Tasks
- [ ] **T1** — In `admin.py` line 99: rename `.order_by(VoiceSession.created_at.desc())` → `.order_by(VoiceSession.started_at.desc())`
- [ ] **T2** — In `sessions.py` `get_session_state` return: rename `created_at=session.created_at` → `started_at=session.started_at`
- [ ] **T3** — Verify `SessionStateResponse` schema uses `started_at: datetime` (already correct — confirm no rename needed in schema)
- [ ] **T4** — Run `pytest tests/` and confirm no `AttributeError` in collection or test run

**Files:** `backend/app/api/admin.py`, `backend/app/api/sessions.py`, `backend/app/schemas/session.py`

---

### IS-02 🔴 Fix `SessionInitResponse` missing required fields on session creation

**Gap ref:** BUG-02  
**Labels:** `bug` `critical` `backend`  
**Milestone:** M1 — Bootable

#### User Story
> **As a** participant opening my survey link,  
> **I want** the session initialization endpoint to return a valid, complete response,  
> **so that** the frontend receives all data it needs to start the voice session without a server error.

#### Context
`SessionInitResponse` schema declares required fields `current_question_index: int` and `state: str`. The `init_session` handler constructs the response without these fields, causing Pydantic to raise `ValidationError` (HTTP 500) on every successful session creation.

#### Acceptance Criteria
- [ ] `POST /api/sessions/init` with a valid invite token returns HTTP 201 (not 500)
- [ ] Response body contains `current_question_index: 0` and `state: "GREETING"`
- [ ] `participant_name` is populated from the participant record (see DOC-06 / IS-29)
- [ ] Integration test `test_session_init_creates_session` passes

#### Tasks
- [ ] **T1** — In `sessions.py` `init_session`, add `current_question_index=0, state=SessionState.GREETING.value` to the `SessionInitResponse(...)` constructor
- [ ] **T2** — Also pass `participant_name=participant.name` to fix DOC-06 simultaneously
- [ ] **T3** — Write/update integration test asserting 201 status and presence of all required fields in response body

**Files:** `backend/app/api/sessions.py`

---

### IS-03 🔴 Fix `QuestionResponse` missing `question_index` (DB NOT NULL violation)

**Gap ref:** BUG-03  
**Labels:** `bug` `critical` `backend`  
**Milestone:** M1 — Bootable

#### User Story
> **As a** survey administrator,  
> **I want** every participant's spoken response to be saved to the database successfully,  
> **so that** no session data is silently lost due to a database integrity error.

#### Context
`Response.question_index` is `nullable=False` in the ORM model. The `QuestionResponse(...)` constructor in `websocket.py` never sets this field. Every `await db.flush()` after a participant response terminates the WebSocket connection with an `IntegrityError`, losing all session data.

#### Acceptance Criteria
- [ ] A complete 3-question session logs exactly 3 `Response` rows in the database
- [ ] Each `Response` row has `question_index` equal to its position (0-based)
- [ ] No `IntegrityError` is raised during a normal session flow
- [ ] Integration test verifies response count and `question_index` values post-session

#### Tasks
- [ ] **T1** — In `websocket.py`, add `question_index=sm.current_question_index` to the `QuestionResponse(...)` constructor call
- [ ] **T2** — Write an integration test that runs a mock 2-question session and asserts all `Response` rows have correct `question_index` values

**Files:** `backend/app/api/websocket.py`

---

### IS-04 🔴 Fix `/api/auth/refresh` to read from httpOnly cookie (not query param)

**Gap ref:** BUG-04  
**Labels:** `bug` `critical` `backend` `security`  
**Milestone:** M1 — Bootable

#### User Story
> **As an** admin user working in the dashboard,  
> **I want** my access token to be silently refreshed using the httpOnly refresh cookie,  
> **so that** I am not logged out mid-session when my 15-minute access token expires.

#### Context
`refresh_access_token` declares `refresh_token: str | None = None` as a plain query parameter instead of reading the `voxora_refresh` httpOnly cookie. The endpoint always raises HTTP 401 because no caller ever passes the token as a query param.

#### Acceptance Criteria
- [ ] `POST /api/auth/refresh` with a valid `voxora_refresh` httpOnly cookie returns a new access token (HTTP 200)
- [ ] `POST /api/auth/refresh` with no cookie returns HTTP 401
- [ ] The frontend `api.js` 401-retry interceptor successfully refreshes and retries the original request
- [ ] A new `voxora_refresh` cookie is set in the response (token rotation)

#### Tasks
- [ ] **T1** — Replace `refresh_token: str | None = None` parameter with `voxora_refresh: str | None = Cookie(None)` (import `Cookie` from `fastapi`)
- [ ] **T2** — Replace `payload = decode_token(refresh_token, ...)` with `payload = decode_token(voxora_refresh, ...)`
- [ ] **T3** — Remove the unused `from fastapi import Request` local import
- [ ] **T4** — Write unit test: mock a request with the cookie set → assert 200 and new access token returned

**Files:** `backend/app/api/auth.py`

---

### IS-05 🔴 Fix auth router prefix duplication (all auth endpoints return 404)

**Gap ref:** DOC-05  
**Labels:** `bug` `critical` `backend`  
**Milestone:** M1 — Bootable

#### User Story
> **As a** developer or admin user,  
> **I want** all auth endpoints to be reachable at `/api/auth/login`, `/api/auth/refresh`, and `/api/auth/logout`,  
> **so that** admin login and token management work correctly.

#### Context
`auth.py` defines `router = APIRouter(prefix="/api/auth", ...)`. `main.py` registers it with `app.include_router(auth_router, prefix="/api/auth", ...)`. Both prefixes combine, making all routes mount at `/api/auth/api/auth/login` — a 404 on the expected paths.

#### Acceptance Criteria
- [ ] `POST /api/auth/login` returns HTTP 200 or 401 (not 404)
- [ ] `POST /api/auth/refresh` is reachable at the documented path
- [ ] `POST /api/auth/logout` is reachable at the documented path
- [ ] Swagger UI (`/docs`) shows all three routes under the `auth` tag with correct paths

#### Tasks
- [ ] **T1** — In `auth.py`, change `router = APIRouter(prefix="/api/auth", ...)` to `router = APIRouter()` (remove `prefix` since `main.py` supplies it)
- [ ] **T2** — Verify all three auth routes appear correctly in `/docs`
- [ ] **T3** — Run `test_login` integration test and confirm HTTP 200/401 response

**Files:** `backend/app/api/auth.py`, `backend/app/main.py`

---

### IS-06 🔴 Add `sample_participant` fixture to test conftest (integration tests uncollectable)

**Gap ref:** BUG-05  
**Labels:** `bug` `critical` `testing`  
**Milestone:** M1 — Bootable

#### User Story
> **As a** developer running the test suite,  
> **I want** all integration test fixtures to be properly defined in `conftest.py`,  
> **so that** pytest can collect and run integration tests without fixture errors.

#### Context
`test_websocket.py` and `test_moderation.py` reference a `sample_participant` fixture not defined anywhere. pytest reports `fixture 'sample_participant' not found` and fails to collect the entire integration module.

#### Acceptance Criteria
- [ ] `pytest tests/integration/` collects all tests without fixture errors
- [ ] `sample_participant` fixture creates a `Participant` linked to `sample_survey` with a valid `invite_token`
- [ ] `test_session_init_creates_session` uses `sample_participant.invite_token` correctly

#### Tasks
- [ ] **T1** — Add `sample_participant` async fixture to `conftest.py` that creates a `Participant` row (`survey_id=sample_survey.id`, `invite_token=secrets.token_urlsafe(32)`, `status="PENDING"`)
- [ ] **T2** — Run `pytest tests/integration/ -v` and confirm all tests are collected

**Files:** `backend/tests/conftest.py`

---

## M2 — Security Deficiencies

---

### IS-07 🔴 Implement server-side refresh token storage and revocation

**Gap ref:** SEC-01  
**Labels:** `security` `high` `backend`  
**Milestone:** M2 — Secure

#### User Story
> **As a** security engineer,  
> **I want** refresh tokens to be stored server-side as hashed values and invalidated on logout,  
> **so that** a stolen refresh token cannot be used after the admin explicitly logs out.

#### Context
`hash_token()` is implemented in `security/auth.py` but never called. Refresh tokens are JWT-only. Logout only deletes the cookie — the token itself is valid until its 7-day expiry regardless.

#### Acceptance Criteria
- [ ] On `POST /api/auth/login`, the SHA-256 hash of the refresh token is stored in the database
- [ ] On `POST /api/auth/refresh`, the incoming token hash is verified against the stored hash; mismatched or missing hash → 401
- [ ] On `POST /api/auth/logout`, the stored hash is deleted; subsequent use of the same refresh token → 401
- [ ] Old refresh token hash is deleted and replaced on every successful refresh (token rotation)
- [ ] Unit test verifies that a refresh token works once, and fails after logout

#### Tasks
- [ ] **T1** — Add `refresh_token_hash: str | None` and `refresh_token_expires_at: datetime | None` columns to `AdminUser` model (or create a separate `RefreshToken` table)
- [ ] **T2** — Write Alembic migration for the new column(s)
- [ ] **T3** — In `login` handler: after creating refresh token, call `hash_token()` and store the hash on the admin record
- [ ] **T4** — In `refresh_access_token` handler: fetch admin, verify `hash_token(incoming_token) == admin.refresh_token_hash`; 401 if mismatch or expired
- [ ] **T5** — In `logout` handler: set `admin.refresh_token_hash = None`, commit
- [ ] **T6** — Write unit tests for all three flows (login, refresh, logout + re-use attempt)

**Files:** `backend/app/models/admin_user.py`, `backend/app/api/auth.py`, `backend/app/security/auth.py`, `backend/alembic/versions/`

---

### IS-08 🔴 Apply rate limiting decorator to session init endpoint

**Gap ref:** SEC-02  
**Labels:** `security` `high` `backend`  
**Milestone:** M2 — Secure

#### User Story
> **As a** security engineer,  
> **I want** the session initialization endpoint to be rate-limited to 10 requests per minute per IP,  
> **so that** brute-force enumeration of invite tokens is prevented.

#### Context
`SlowAPIMiddleware` is registered in `main.py` and the `limiter` singleton is created, but no `@limiter.limit()` decorator is applied to any route. The `/api/sessions/init` endpoint is completely unprotected.

#### Acceptance Criteria
- [ ] More than 10 `POST /api/sessions/init` requests from the same IP within 60 seconds returns HTTP 429
- [ ] The 429 response includes a `Retry-After` header
- [ ] Normal usage (< 10 req/min) is not affected
- [ ] Rate limit is configurable via `settings` (not hard-coded)

#### Tasks
- [ ] **T1** — Add `from app.security.rate_limiter import limiter` import to `sessions.py`
- [ ] **T2** — Add `@limiter.limit("10/minute")` decorator to `init_session` route
- [ ] **T3** — Add `request: Request` parameter to `init_session` (required by SlowAPI)
- [ ] **T4** — Add a `session_init_rate_limit` setting to `config.py` (default `"10/minute"`) and use it in the decorator
- [ ] **T5** — Write an integration test that sends 11 requests from the same IP and asserts the 11th returns 429

**Files:** `backend/app/api/sessions.py`, `backend/app/config.py`, `backend/app/security/rate_limiter.py`

---

### IS-09 🔴 Implement per-IP WebSocket connection limit enforcement

**Gap ref:** SEC-03  
**Labels:** `security` `medium` `backend`  
**Milestone:** M2 — Secure

#### User Story
> **As a** security engineer,  
> **I want** the WebSocket endpoint to reject connections from IPs that already have 5+ active sessions,  
> **so that** a single client cannot exhaust server resources through connection flooding.

#### Context
`max_ws_connections_per_ip = 5` is defined in `Settings` but never read. The WebSocket handler has no connection registry.

#### Acceptance Criteria
- [ ] A 6th concurrent WebSocket connection from the same IP is rejected with close code `1008`
- [ ] When a WebSocket disconnects, its IP's connection count is decremented in Redis
- [ ] Connection count is consistent even if the process restarts (counts stored in Redis, not memory)
- [ ] The limit is configurable via `settings.max_ws_connections_per_ip`

#### Tasks
- [ ] **T1** — Define Redis key pattern: `ws_connections:{ip_address}` (integer counter with TTL)
- [ ] **T2** — On WebSocket connect: `INCR ws_connections:{ip}`. If result > `settings.max_ws_connections_per_ip`, close with code 1008
- [ ] **T3** — On WebSocket disconnect (both graceful and `WebSocketDisconnect`): `DECR ws_connections:{ip}` with floor at 0
- [ ] **T4** — Write a unit test mocking the Redis counter to verify rejection at limit + 1

**Files:** `backend/app/api/websocket.py`, `backend/app/config.py`

---

## M3 — Database Infrastructure

---

### IS-10 🔴 Generate Alembic migration files for all database tables and indexes

**Gap ref:** FEAT-01  
**Labels:** `infrastructure` `high` `database`  
**Milestone:** M3 — Database

#### User Story
> **As a** developer or DevOps engineer,  
> **I want** to create the complete database schema by running `alembic upgrade head`,  
> **so that** any fresh environment can reproduce the exact production schema without manual SQL.

#### Context
`alembic/versions/` contains only a `.gitkeep`. All 6 tables exist only as ORM models. There is no migration to run. A fresh `docker compose up` will start the app with no tables and crash on the first database operation.

#### Acceptance Criteria
- [ ] `alembic upgrade head` on a blank PostgreSQL instance creates all 6 tables: `surveys`, `questions`, `participants`, `sessions`, `responses`, `admin_users`
- [ ] All constraints (FK, UNIQUE, NOT NULL) are enforced after migration
- [ ] All documented indexes are present: `participants.invite_token`, `participants.status`, `participants.survey_id`, `sessions.participant_id`, `responses.session_id`, `responses.question_id`
- [ ] `alembic downgrade -1` cleanly reverts the migration
- [ ] A second migration for `AdminUser.refresh_token_hash` column is also created (required by IS-07)

#### Tasks
- [ ] **T1** — Configure `alembic/env.py` to reference all models via `Base.metadata` (verify current state)
- [ ] **T2** — Run `alembic revision --autogenerate -m "initial_schema"` and review the generated diff
- [ ] **T3** — Manually verify the generated migration includes all 6 tables, all columns, all FK constraints, and UNIQUE constraints
- [ ] **T4** — Add the performance indexes manually if `--autogenerate` does not include them
- [ ] **T5** — Run `alembic upgrade head` against a test PostgreSQL instance and verify with `\dt` / `\di`
- [ ] **T6** — Run `alembic downgrade -1` and confirm tables are removed cleanly

**Files:** `backend/alembic/versions/`, `backend/alembic/env.py`

---

## M4 — Feature Completeness

---

### IS-11 🔴 Implement session reconnect and status guard in session init

**Gap ref:** FEAT-02  
**Labels:** `feature` `high` `backend`  
**Milestone:** M4 — Correct

#### User Story
> **As a** participant whose connection drops mid-interview,  
> **I want** to re-open my survey link and continue from where I left off,  
> **so that** a temporary network issue does not force me to restart the entire interview.

> **As a** security engineer,  
> **I want** flagged participants to be blocked from starting new sessions,  
> **so that** participants whose sessions were terminated for policy violations cannot re-enter.

#### Context
`init_session` checks only `COMPLETED` and `EXPIRED` status. `IN_PROGRESS` participants get a duplicate session created. `FLAGGED` participants can freely re-enter.

#### Acceptance Criteria
- [ ] `POST /api/sessions/init` for a `COMPLETED` participant returns HTTP 409
- [ ] `POST /api/sessions/init` for an `EXPIRED` participant returns HTTP 410
- [ ] `POST /api/sessions/init` for a `FLAGGED` participant returns HTTP 403 with a neutral message
- [ ] `POST /api/sessions/init` for an `IN_PROGRESS` participant returns HTTP 200 with the **existing** session's token (no new session created)
- [ ] Reconnect path restores `current_question_index` from Redis state machine or DB
- [ ] Each reconnect scenario has a corresponding unit test

#### Tasks
- [ ] **T1** — Add `FLAGGED` status check: raise HTTP 403 `"This session has been ended."` before creating a new session
- [ ] **T2** — Add `IN_PROGRESS` status check: query for the most recent active session for this participant; if found, generate a new short-lived JWT for that session and return it (reconnect response)
- [ ] **T3** — Ensure `total_questions`, `persona`, and `current_question_index` are populated from the existing session in the reconnect response
- [ ] **T4** — Write 4 unit tests covering each edge case (COMPLETED, EXPIRED, FLAGGED, IN_PROGRESS reconnect)

**Files:** `backend/app/api/sessions.py`

---

### IS-12 🔴 Implement `PUT /api/surveys/{id}/questions/{q_id}` endpoint

**Gap ref:** FEAT-03  
**Labels:** `feature` `medium` `backend`  
**Milestone:** M4 — Correct

#### User Story
> **As an** admin,  
> **I want** to update the text, type, or follow-up prompt of an existing survey question via the API,  
> **so that** I can correct mistakes or refine questions without deleting and recreating them.

#### Acceptance Criteria
- [ ] `PUT /api/surveys/{id}/questions/{q_id}` accepts a partial update payload (all fields optional)
- [ ] Returns the updated `Question` object with HTTP 200
- [ ] Returns HTTP 404 if either the survey or question does not exist
- [ ] Returns HTTP 403 if the question does not belong to the specified survey
- [ ] Requires admin authentication
- [ ] Endpoint is documented in Swagger UI

#### Tasks
- [ ] **T1** — Create `QuestionUpdate` Pydantic schema in `schemas/survey.py` with all optional fields: `question_text`, `question_type`, `expected_topics`, `follow_up_text`
- [ ] **T2** — Implement `PUT /{survey_id}/questions/{question_id}` route in `surveys.py`
- [ ] **T3** — Validate that the question's `survey_id` matches the URL `survey_id` (prevent cross-survey edits)
- [ ] **T4** — Write unit tests: successful update, 404 on missing question, 403 on wrong survey

**Files:** `backend/app/api/surveys.py`, `backend/app/schemas/survey.py`

---

### IS-13 🔴 Implement question `order_index` rebalancing after delete

**Gap ref:** FEAT-04  
**Labels:** `feature` `medium` `backend`  
**Milestone:** M4 — Correct

#### User Story
> **As an** admin,  
> **I want** question order indices to be contiguous after a question is deleted,  
> **so that** the state machine's sequential index logic always maps correctly to the question list.

#### Context
Deleting question at index 2 from a [1, 2, 3, 4] sequence leaves [1, 3, 4]. The state machine uses `current_question_index` as a list offset, so this gap causes the wrong question to be asked or an `IndexError`.

#### Acceptance Criteria
- [ ] After deleting question at `order_index=2` from a 4-question survey, remaining questions are re-ordered to `[1, 2, 3]`
- [ ] Order rebalancing uses a single database UPDATE (not N queries)
- [ ] The deletion + rebalancing is atomic (single transaction)
- [ ] Integration test verifies order integrity after deletion

#### Tasks
- [ ] **T1** — After deleting the question row, execute: `UPDATE questions SET order_index = order_index - 1 WHERE survey_id = :survey_id AND order_index > :deleted_index`
- [ ] **T2** — Wrap deletion + rebalance in a single `async with db.begin():` block
- [ ] **T3** — Write a test: create 4 questions, delete index 2, assert remaining questions have contiguous indices [1, 2, 3]

**Files:** `backend/app/api/surveys.py`

---

### IS-14 🔴 Wire recent-persona DB query to prevent persona repetition

**Gap ref:** FEAT-05  
**Labels:** `feature` `medium` `backend`  
**Milestone:** M4 — Correct

#### User Story
> **As a** participant who takes multiple surveys on the Voxora platform,  
> **I want** to be assigned a different AI persona each time I participate,  
> **so that** the experience feels varied and does not feel repetitive.

#### Context
`PersonaManager.assign_random(recent_persona_names=[...])` supports non-repetition, but `init_session` calls it with no arguments. The participant's session history is never queried.

#### Acceptance Criteria
- [ ] When a participant has previous sessions, their last 3 persona names are retrieved from the database
- [ ] The newly assigned persona is never one of the last 3 (unless pool exhaustion forces a repeat)
- [ ] First-time participants are unaffected (empty list passed, random selection from full pool)
- [ ] Unit test verifies that `assign_random` receives the correct `recent_persona_names` argument

#### Tasks
- [ ] **T1** — In `init_session`, query the participant's previous sessions ordered by `started_at DESC LIMIT 3`
- [ ] **T2** — Extract `[session.persona["name"] for session in recent_sessions]`
- [ ] **T3** — Pass the list to `persona_manager.assign_random(recent_persona_names=recent_names)`
- [ ] **T4** — Write a unit test with a mocked DB returning 3 prior sessions; assert `assign_random` is called with the correct names

**Files:** `backend/app/api/sessions.py`

---

### IS-15 🔴 Implement Redis WebSocket connection registry

**Gap ref:** FEAT-09  
**Labels:** `feature` `medium` `backend` `infrastructure`  
**Milestone:** M4 — Correct

#### User Story
> **As a** backend engineer,  
> **I want** active WebSocket connections to be registered in Redis on connect and deregistered on disconnect,  
> **so that** per-IP connection limits (IS-09) can be reliably enforced and ops teams can monitor active sessions.

#### Context
IS-09 (per-IP limit) and general session monitoring both depend on a registry. Currently no Redis keys track active WS connections.

#### Acceptance Criteria
- [ ] On WebSocket accept: Redis key `ws_connections:{ip_address}` is incremented via `INCR` with a TTL of `SESSION_STATE_TTL + 60` seconds
- [ ] On WebSocket close (both graceful and disconnect): the counter is decremented (floor at 0)
- [ ] Counter is shared across processes (Redis, not in-memory)
- [ ] IS-09 reads from this same counter

#### Tasks
- [ ] **T1** — Extract client IP in the WebSocket handler (from `websocket.headers.get("x-forwarded-for")` or `websocket.client.host`)
- [ ] **T2** — After `websocket.accept()`: `await redis.incr(f"ws_connections:{client_ip}")`; set TTL if this is the first connection
- [ ] **T3** — In all exit paths (normal close, `WebSocketDisconnect`, exception): `await redis.decr(f"ws_connections:{client_ip}")`
- [ ] **T4** — Link IS-09 to read from this counter for the limit check (coordinate implementation)

**Files:** `backend/app/api/websocket.py`

---

### IS-16 🔴 Implement Whisper confidence threshold with re-ask logic

**Gap ref:** FEAT-10  
**Labels:** `feature` `medium` `backend`  
**Milestone:** M4 — Correct

#### User Story
> **As a** participant whose answer was only partially captured,  
> **I want** the AI interviewer to politely ask me to repeat myself,  
> **so that** my actual answer is recorded rather than a garbled or incomplete transcript.

#### Context
`transcribe()` uses `response_format="text"`, which returns a plain string with no confidence data. Confidence-based re-ask requires `response_format="verbose_json"` to obtain per-segment confidence scores.

#### Acceptance Criteria
- [ ] Transcriptions with average confidence < 0.70 trigger a re-ask using `get_repeat_request()`
- [ ] Up to 3 re-ask attempts are made before the question is skipped
- [ ] The confidence score is logged to `Response.sentiment_score` (or a dedicated field) for quality analysis
- [ ] Transcriptions with no audio (empty segments) are still caught by the existing empty-transcript check

#### Tasks
- [ ] **T1** — Change `response_format="text"` → `response_format="verbose_json"` in `ai_orchestrator.transcribe()`
- [ ] **T2** — Parse `response.segments` to calculate average `avg_logprob` (Whisper's confidence proxy); convert to 0–1 range: `confidence = min(1.0, max(0.0, 1 + avg_logprob / 5))`
- [ ] **T3** — Return `(transcript: str, confidence: float)` tuple from `transcribe()`
- [ ] **T4** — In `websocket.py` turn loop: if `confidence < settings.whisper_confidence_threshold` (default 0.70), send re-ask audio and `continue`
- [ ] **T5** — Add `whisper_confidence_threshold: float = 0.70` to `Settings`
- [ ] **T6** — Write unit tests for confidence calculation at boundary values (0.0, 0.69, 0.70, 1.0)

**Files:** `backend/app/services/ai_orchestrator.py`, `backend/app/api/websocket.py`, `backend/app/config.py`

---

### IS-17 🔴 Add frontend unit and component tests

**Gap ref:** FEAT-13  
**Labels:** `testing` `medium` `frontend`  
**Milestone:** M5 — Quality

#### User Story
> **As a** frontend developer,  
> **I want** a unit test suite for critical hooks and components,  
> **so that** regressions in the voice session lifecycle, VAD, and auth flow are caught before deployment.

#### Acceptance Criteria
- [ ] Vitest + React Testing Library are installed and configured
- [ ] `npm test` runs successfully in CI with at least 10 test cases passing
- [ ] `useVAD` hook is tested: speech start fires after `SPEECH_START_FRAMES` above threshold; speech end fires after `SILENCE_FRAMES_END` below threshold
- [ ] `useAdminAuth` hook is tested: login sets token in store; logout clears token
- [ ] `SurveyPage` component is tested: renders consent stage on load; transitions to SESSION stage on consent
- [ ] `LoginPage` is tested: shows error message on failed login; redirects on success
- [ ] `SessionStore` is tested: `reset()` clears all state; persisted keys are `questionIndex` and `totalQuestions` only

#### Tasks
- [ ] **T1** — Add `vitest`, `@vitest/ui`, `jsdom`, `@testing-library/react`, `@testing-library/user-event`, `@testing-library/jest-dom` to `package.json` devDependencies
- [ ] **T2** — Configure `vite.config.js` test environment: `test: { environment: 'jsdom', setupFiles: ['./src/test/setup.js'] }`
- [ ] **T3** — Create `src/test/setup.js` importing `@testing-library/jest-dom`
- [ ] **T4** — Write `src/hooks/__tests__/useVAD.test.js`
- [ ] **T5** — Write `src/hooks/__tests__/useAdminAuth.test.js`
- [ ] **T6** — Write `src/pages/__tests__/SurveyPage.test.jsx`
- [ ] **T7** — Write `src/pages/__tests__/LoginPage.test.jsx`
- [ ] **T8** — Write `src/store/__tests__/sessionStore.test.js`
- [ ] **T9** — Update `.github/workflows/ci.yml` `frontend-build` job to run `npm test -- --run` before the build step

**Files:** `frontend/package.json`, `frontend/vite.config.js`, `frontend/src/test/`, `frontend/src/hooks/__tests__/`, `frontend/src/pages/__tests__/`, `frontend/src/store/__tests__/`, `.github/workflows/ci.yml`

---

### IS-18 🔴 Implement audio storage integration (S3/object store)

**Gap ref:** FEAT-06  
**Labels:** `feature` `medium` `backend` `infrastructure`  
**Milestone:** M4 — Correct

#### User Story
> **As a** survey administrator,  
> **I want** each participant's raw audio to be stored in cloud object storage and linked to their response record,  
> **so that** I can review the original recordings to verify transcript accuracy or resolve disputes.

#### Acceptance Criteria
- [ ] After transcription, audio bytes are uploaded to S3 (or S3-compatible storage)
- [ ] `Response.audio_url` is populated with the object's public or pre-signed URL
- [ ] Upload failure is non-fatal (logged as a warning, session continues)
- [ ] Storage credentials are injected via environment variables (`S3_BUCKET`, `AWS_ACCESS_KEY_ID`, etc.)
- [ ] Local development can use MinIO (configured in `docker-compose.yml`)

#### Tasks
- [ ] **T1** — Add S3 settings to `config.py`: `s3_bucket`, `s3_region`, `aws_access_key_id`, `aws_secret_access_key`, `s3_endpoint_url` (for MinIO)
- [ ] **T2** — Create `backend/app/services/storage_service.py` with `async def upload_audio(session_id, question_index, audio_bytes) -> str | None`
- [ ] **T3** — Use `aioboto3` (async boto3 wrapper) to upload; key pattern: `audio/{session_id}/q{question_index}.webm`
- [ ] **T4** — In `websocket.py` turn loop: after transcription, call `storage_service.upload_audio(...)` and pass result to `QuestionResponse.audio_url`
- [ ] **T5** — Add MinIO service to `docker-compose.yml` for local dev
- [ ] **T6** — Write a unit test with a mocked S3 client asserting upload is called with correct key and bytes

**Files:** `backend/app/services/storage_service.py` (new), `backend/app/config.py`, `backend/app/api/websocket.py`, `docker-compose.yml`

---

### IS-19 🔴 Implement sentiment analysis on participant responses

**Gap ref:** FEAT-07  
**Labels:** `feature` `low` `backend`  
**Milestone:** M4 — Correct

#### User Story
> **As a** survey administrator,  
> **I want** each participant's transcript response to include a sentiment score,  
> **so that** I can quickly identify positive, neutral, and negative patterns across the survey data without reading every transcript.

#### Acceptance Criteria
- [ ] `Response.sentiment_score` is populated (range: -1.0 negative to 1.0 positive) for every logged response
- [ ] Sentiment analysis is performed asynchronously and does not block the session turn
- [ ] The score is visible in the `ResponseViewer` admin component
- [ ] Sentiment analysis failure is non-fatal (score remains `null` if the service is unavailable)

#### Tasks
- [ ] **T1** — Create `backend/app/services/sentiment_service.py` using a lightweight approach: either GPT-4o-mini with a structured JSON output prompt for sentiment, or a local `textblob`/`vaderSentiment` library (no external API call)
- [ ] **T2** — In `websocket.py` turn loop: after logging the response, fire an `asyncio.create_task()` for `sentiment_service.score(transcript)` and update the record asynchronously
- [ ] **T3** — Alternatively: add a background task via FastAPI's `BackgroundTasks` to score after response
- [ ] **T4** — Expose `sentiment_score` in `ResponseViewer.jsx` alongside the transcript

**Files:** `backend/app/services/sentiment_service.py` (new), `backend/app/api/websocket.py`, `frontend/src/components/admin/ResponseViewer.jsx`

---

## M5 — Quality, Documentation and DevOps

---

### IS-20 🔴 Fix CI workflow to trigger on `develop` branch pull requests

**Gap ref:** DOC-04  
**Labels:** `devops` `low`  
**Milestone:** M5 — Quality

#### User Story
> **As a** developer opening a pull request to the `develop` branch,  
> **I want** the CI pipeline to run automatically,  
> **so that** code quality is verified before the PR is reviewed.

#### Acceptance Criteria
- [ ] A pull request targeting `develop` triggers the CI `backend-lint-test` and `frontend-build` jobs
- [ ] A pull request targeting `main` continues to trigger CI (existing behaviour retained)

#### Tasks
- [ ] **T1** — In `.github/workflows/ci.yml`, change `branches: [main]` to `branches: [main, develop]`

**Files:** `.github/workflows/ci.yml`

---

### IS-21 🔴 Add average session duration KPI to admin stats endpoint

**Gap ref:** FEAT-12  
**Labels:** `feature` `low` `backend` `frontend`  
**Milestone:** M5 — Quality

#### User Story
> **As a** survey administrator,  
> **I want** the dashboard overview to show the average session completion time,  
> **so that** I can assess how long the survey takes and identify if it is too long for participants.

#### Acceptance Criteria
- [ ] `GET /api/admin/stats` response includes `avg_session_duration_seconds: float | None`
- [ ] The value is the average of `duration_seconds` for all `COMPLETED` sessions (NULL excluded)
- [ ] `StatsOverview.jsx` displays the formatted average duration (e.g., "4m 32s")
- [ ] Returns `null` if no completed sessions exist yet

#### Tasks
- [ ] **T1** — Add `avg_session_duration_seconds: float | None` to `AdminStats` Pydantic schema
- [ ] **T2** — In `get_stats`, add: `avg_dur = (await db.execute(select(func.avg(VoiceSession.duration_seconds)).where(VoiceSession.state == 'COMPLETED'))).scalar_one_or_none()`
- [ ] **T3** — Include `avg_session_duration_seconds=avg_dur` in the `AdminStats(...)` return
- [ ] **T4** — In `StatsOverview.jsx`, add a KPI card displaying the formatted duration

**Files:** `backend/app/api/admin.py`, `backend/app/schemas/admin.py`, `frontend/src/components/admin/StatsOverview.jsx`

---

### IS-22 🔴 Implement audio energy "too quiet" detection in WebSocket handler

**Gap ref:** FEAT-11  
**Labels:** `feature` `low` `backend`  
**Milestone:** M5 — Quality

#### User Story
> **As a** participant speaking quietly,  
> **I want** the AI to gently let me know if my microphone volume is too low,  
> **so that** I can adjust before my answer is lost.

#### Acceptance Criteria
- [ ] Audio frames below a configurable RMS energy threshold trigger a "Could you speak a little louder?" response
- [ ] The threshold is configurable via `settings.audio_energy_threshold` (default: `0.001`)
- [ ] This check occurs before the Whisper transcription call (no unnecessary API usage)
- [ ] A max of 2 consecutive "too quiet" prompts are given before the question is treated as a skip

#### Tasks
- [ ] **T1** — Add `audio_energy_threshold: float = 0.001` to `Settings`
- [ ] **T2** — After receiving `audio_bytes` in the WebSocket handler, calculate RMS: `import struct; rms = sqrt(sum(x**2 for x in struct.unpack(...)) / n)`
- [ ] **T3** — If `rms < settings.audio_energy_threshold`, synthesize "too quiet" message and `continue`
- [ ] **T4** — Track consecutive quiet count; after 2 → skip the question
- [ ] **T5** — Add `get_too_quiet_message()` function to `refocus_templates.py`

**Files:** `backend/app/api/websocket.py`, `backend/app/config.py`, `backend/app/prompts/refocus_templates.py`

---

### IS-23 🔴 Integrate ElevenLabs TTS as a configurable TTS provider

**Gap ref:** FEAT-08  
**Labels:** `feature` `low` `backend`  
**Milestone:** M5 — Quality

#### User Story
> **As a** survey administrator,  
> **I want** to optionally switch the text-to-speech provider to ElevenLabs,  
> **so that** AI personas can have more realistic and distinctive voices than the standard OpenAI TTS voices.

#### Acceptance Criteria
- [ ] When `elevenlabs_enabled=true` and `elevenlabs_api_key` is set, TTS uses the ElevenLabs API
- [ ] When `elevenlabs_enabled=false` (default), OpenAI TTS is used as before
- [ ] Persona `voice_id` values are mapped to appropriate ElevenLabs voice IDs in `personas.yaml`
- [ ] ElevenLabs API errors fall back to OpenAI TTS with a warning log

#### Tasks
- [ ] **T1** — Create `backend/app/services/elevenlabs_service.py` with `async def synthesize(text, voice_id) -> bytes`
- [ ] **T2** — In `AIOrchestratorService.synthesize_speech()`, check `settings.elevenlabs_enabled`; route to ElevenLabs or OpenAI accordingly
- [ ] **T3** — Add ElevenLabs voice IDs to `personas.yaml` as a secondary `el_voice_id` field
- [ ] **T4** — Write a unit test for provider routing logic

**Files:** `backend/app/services/elevenlabs_service.py` (new), `backend/app/services/ai_orchestrator.py`, `backend/app/prompts/personas.yaml`

---

### IS-24 🔴 Add pre-commit hook configuration

**Gap ref:** FEAT-14  
**Labels:** `devops` `low`  
**Milestone:** M5 — Quality

#### User Story
> **As a** developer,  
> **I want** `black`, `ruff`, and `eslint` to run automatically before every commit,  
> **so that** code style violations are caught locally before they reach CI.

#### Acceptance Criteria
- [ ] `pre-commit install` sets up hooks in < 30 seconds
- [ ] `git commit` on a Python file with `ruff` errors is rejected with a clear message
- [ ] `git commit` on a JavaScript file with `eslint` errors is rejected with a clear message
- [ ] `black` auto-formats Python files on commit

#### Tasks
- [ ] **T1** — Create `.pre-commit-config.yaml` at repo root with hooks: `pre-commit-hooks` (trailing-whitespace, end-of-file-fixer), `black` (language_version: python3.12), `ruff`, `eslint` (for JS files)
- [ ] **T2** — Add `pre-commit` to `backend/requirements-dev.txt`
- [ ] **T3** — Add setup step to `README.md` Getting Started section: `pip install pre-commit && pre-commit install`

**Files:** `.pre-commit-config.yaml` (new), `backend/requirements-dev.txt`, `README.md`

---

### IS-25 🔴 Add GitHub Pull Request template

**Gap ref:** FEAT-14 (partial)  
**Labels:** `devops` `low`  
**Milestone:** M5 — Quality

#### User Story
> **As a** developer submitting a pull request,  
> **I want** a PR template that prompts me to fill in a description, testing steps, and gap-analysis reference,  
> **so that** all PRs have consistent, reviewable descriptions.

#### Acceptance Criteria
- [ ] Opening a new GitHub PR pre-fills the description with the template
- [ ] Template includes sections: Summary, Gap Ref, Type of Change (checklist), Testing, Checklist

#### Tasks
- [ ] **T1** — Create `.github/PULL_REQUEST_TEMPLATE.md`

**Files:** `.github/PULL_REQUEST_TEMPLATE.md` (new)

---

### IS-26 🔴 Update README route parameter from `:participantId` to `:inviteToken`

**Gap ref:** DOC-01  
**Labels:** `documentation` `low`  
**Milestone:** M5 — Quality

#### User Story
> **As a** developer reading the README to understand the URL scheme,  
> **I want** the documented route path to match the actual frontend implementation,  
> **so that** I set up invitation URLs with the correct parameter name.

#### Acceptance Criteria
- [ ] All occurrences of `/survey/:participantId` in `README.md` are replaced with `/survey/:inviteToken`
- [ ] The invite URL formatter example uses the `invite_token` field, not a participant UUID

#### Tasks
- [ ] **T1** — Search-and-replace all instances of `:participantId` → `:inviteToken` in `README.md`
- [ ] **T2** — Update invite URL formatter example to reference `invite_token`

**Files:** `README.md`

---

### IS-27 🔴 Update state machine diagram in README to include `PROCESSING` state

**Gap ref:** DOC-02  
**Labels:** `documentation` `low`  
**Milestone:** M5 — Quality

#### User Story
> **As a** developer reading the architecture documentation,  
> **I want** the state machine diagram to match the actual implementation,  
> **so that** I understand the full lifecycle of a session turn.

#### Acceptance Criteria
- [ ] README Section 5.3 state diagram includes `PROCESSING` between `LISTENING` and `LOGGING`
- [ ] WBS T3.2.1.1 state enum list includes `PROCESSING`

#### Tasks
- [ ] **T1** — Update the state machine sequence diagram in `README.md` Section 5.3
- [ ] **T2** — Update the state enum list in `WORK_BREAKDOWN_STRUCTURE.md` T3.2.1.1

**Files:** `README.md`, `WORK_BREAKDOWN_STRUCTURE.md`

---

### IS-28 🔴 Clarify `GET /api/sessions/{id}` access control in documentation

**Gap ref:** DOC-03  
**Labels:** `documentation` `medium`  
**Milestone:** M5 — Quality

#### User Story
> **As a** developer implementing the frontend reconnect flow,  
> **I want** the API documentation to clearly state that `GET /api/sessions/{id}` requires admin auth,  
> **so that** I do not waste time trying to call it from the participant frontend.

#### Acceptance Criteria
- [ ] WBS T2.4.1.5 is updated to indicate this endpoint is admin-protected
- [ ] A separate participant-facing session state endpoint is either specified or the reconnect flow is re-designed to use the existing session init reconnect logic (IS-11)

#### Tasks
- [ ] **T1** — Update `WORK_BREAKDOWN_STRUCTURE.md` T2.4.1.5 to document the endpoint as admin-only
- [ ] **T2** — Decide and document: should the reconnect flow use `POST /api/sessions/init` (returning existing session) OR a new public `GET /api/sessions/state/{invite_token}` endpoint? Update WBS accordingly.

**Files:** `WORK_BREAKDOWN_STRUCTURE.md`

---

### IS-29 🔴 Populate `participant_name` in `SessionInitResponse`

**Gap ref:** DOC-06  
**Labels:** `bug` `low` `backend`  
**Milestone:** M5 — Quality

#### User Story
> **As a** participant opening my survey,  
> **I want** the AI's greeting to use my name,  
> **so that** the session feels personalized from the very first interaction.

#### Acceptance Criteria
- [ ] `POST /api/sessions/init` response includes `participant_name` equal to the participant's `name` field (or `null` if not set)
- [ ] The `PersonaCard` greeting in the frontend displays the participant's name if available

#### Tasks
- [ ] **T1** — In `sessions.py` `init_session` response constructor, add `participant_name=participant.name` (this is combined with IS-02/T2)
- [ ] **T2** — Verify `PersonaCard.jsx` renders the name from `sessionData.participant_name`

**Files:** `backend/app/api/sessions.py`, `frontend/src/components/survey/PersonaCard.jsx`

---

### IS-30 🔴 Replace `<a>` tags with React Router `<Link>` in admin navigation

**Gap ref:** DOC-08  
**Labels:** `code-quality` `low` `frontend`  
**Milestone:** M5 — Quality

#### User Story
> **As an** admin user navigating the dashboard,  
> **I want** sidebar navigation to use client-side routing without full page reloads,  
> **so that** the admin experience is fast and responsive.

#### Acceptance Criteria
- [ ] Navigating between dashboard sections (Dashboard / Participants / Reminders) does not trigger a full page reload
- [ ] The `NavItem` component uses `NavLink` from `react-router-dom` with active state styling
- [ ] All existing route paths continue to work

#### Tasks
- [ ] **T1** — In `AdminPage.jsx`, import `NavLink` from `react-router-dom`
- [ ] **T2** — Replace `<a href={href}>` in the `NavItem` component with `<NavLink to={href} className={({ isActive }) => ...}>`
- [ ] **T3** — Remove the `active` prop from `NavItem` (use `NavLink`'s built-in `isActive` instead)

**Files:** `frontend/src/pages/AdminPage.jsx`

---

## Tracking Summary

| Issue | Title | Category | Severity | Milestone | Status |
|---|---|---|---|---|---|
| IS-01 | Fix Session `started_at`/`created_at` mismatch | Bug | Critical | M1 | 🔴 Open |
| IS-02 | Fix SessionInitResponse missing required fields | Bug | Critical | M1 | 🔴 Open |
| IS-03 | Fix QuestionResponse missing `question_index` | Bug | Critical | M1 | 🔴 Open |
| IS-04 | Fix /auth/refresh to read httpOnly cookie | Bug | Critical | M1 | 🔴 Open |
| IS-05 | Fix auth router prefix duplication | Bug | Critical | M1 | 🔴 Open |
| IS-06 | Add sample_participant test fixture | Testing | Critical | M1 | 🔴 Open |
| IS-07 | Implement refresh token server-side revocation | Security | High | M2 | 🔴 Open |
| IS-08 | Apply rate limiting to session init endpoint | Security | High | M2 | 🔴 Open |
| IS-09 | Enforce per-IP WebSocket connection limit | Security | Medium | M2 | 🔴 Open |
| IS-10 | Generate Alembic migration files | Infrastructure | High | M3 | 🔴 Open |
| IS-11 | Implement session reconnect + status guard | Feature | High | M4 | 🔴 Open |
| IS-12 | Implement PUT /questions/{q_id} endpoint | Feature | Medium | M4 | 🔴 Open |
| IS-13 | Implement question order rebalancing on delete | Feature | Medium | M4 | 🔴 Open |
| IS-14 | Wire recent-persona DB query in session init | Feature | Medium | M4 | 🔴 Open |
| IS-15 | Implement Redis WebSocket connection registry | Feature | Medium | M4 | 🔴 Open |
| IS-16 | Implement Whisper confidence threshold re-ask | Feature | Medium | M4 | 🔴 Open |
| IS-17 | Add frontend unit and component tests | Testing | Medium | M5 | 🔴 Open |
| IS-18 | Implement audio storage (S3/object store) | Feature | Medium | M4 | 🔴 Open |
| IS-19 | Implement sentiment analysis on responses | Feature | Low | M4 | 🔴 Open |
| IS-20 | Fix CI to trigger on `develop` branch | DevOps | Low | M5 | 🔴 Open |
| IS-21 | Add avg session duration KPI to admin stats | Feature | Low | M5 | 🔴 Open |
| IS-22 | Implement audio energy "too quiet" detection | Feature | Low | M5 | 🔴 Open |
| IS-23 | Integrate ElevenLabs TTS provider | Feature | Low | M5 | 🔴 Open |
| IS-24 | Add pre-commit hook configuration | DevOps | Low | M5 | 🔴 Open |
| IS-25 | Add GitHub PR template | DevOps | Low | M5 | 🔴 Open |
| IS-26 | Update README route param `:participantId` → `:inviteToken` | Docs | Low | M5 | 🔴 Open |
| IS-27 | Update state machine diagram to include PROCESSING | Docs | Low | M5 | 🔴 Open |
| IS-28 | Clarify GET /sessions/{id} access control in docs | Docs | Medium | M5 | 🔴 Open |
| IS-29 | Populate participant_name in SessionInitResponse | Bug | Low | M5 | 🔴 Open |
| IS-30 | Replace `<a>` with `<Link>` in admin navigation | Code Quality | Low | M5 | 🔴 Open |

---

## How to Update This Tracker

When an issue is resolved, update the **Status** column and check off completed tasks within the issue section:
- Change `🔴 Open` → `🟡 In Progress` when work starts
- Change `🟡 In Progress` → `🟢 Done` when merged to `master`
- Note the commit SHA or PR number next to `🟢 Done`

---

*Tracker generated from [IMPLEMENTATION_GAP_ANALYSIS.md](IMPLEMENTATION_GAP_ANALYSIS.md) — April 23, 2026*
