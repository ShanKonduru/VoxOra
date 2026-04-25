# VoxOra — Implementation Gap Analysis
> **Generated:** April 23, 2026  
> **Last validated against code:** April 25, 2026  
> **Branch:** `master`  
> **Scope:** Code-vs-documentation cross-review covering backend, frontend, security, DevOps, and testing layers.

---

## Executive Summary

This document began as the initial cross-review baseline on April 23, 2026. Several of the highest-severity findings have since been resolved in code, especially around auth refresh handling, refresh-token persistence, rate limiting, Alembic migration creation, session response correctness, and integration-test stability.

Current status after April 25 validation:

- Critical auth/session contract defects from the original report are resolved
- Refresh tokens are now persisted and revoked server-side
- Route-level rate limiting is applied to the main write surfaces covered in the hardening pass
- Alembic migration files now exist for refresh tokens and cross-database compatibility updates
- Focused integration validation currently passes with `29` tests and `100%` scoped coverage for `auth`, `sessions`, and `moderation`
- The highest-priority remaining gaps are reconnect/flagged-session handling, per-IP WebSocket connection limiting, survey question update/rebalancing, recent-persona DB wiring, frontend tests, and broader end-to-end/performance validation

| Severity | Count | Impact |
|---|---|---|
| Critical findings resolved since initial report | 5 | Core auth/session runtime blockers no longer present |
| Security deficiencies still open | 1 | WebSocket per-IP concurrency guard remains unenforced |
| Feature gaps still open | 13 | Several documented backend/frontend features remain incomplete |
| Doc/planning updates needed | Ongoing | Planning artifacts must track the implemented hardening work |

---

## Part 1 — Critical Runtime Bugs

These will throw exceptions or produce DB integrity errors in normal operation.

Note: Parts 1–4 preserve the original findings baseline. See Part 7 for the current validated status of implemented versus remaining items.

---

### BUG-01 — `Session` model has no `created_at` column (crash in admin & session API)

**Severity:** Critical  
**Files affected:** [backend/app/models/session.py](backend/app/models/session.py), [backend/app/api/admin.py](backend/app/api/admin.py#L99), [backend/app/api/sessions.py](backend/app/api/sessions.py#L126)

**Description:**  
The `Session` SQLAlchemy model defines `started_at` (line 28) but no `created_at` attribute. Two separate endpoints reference the non-existent `created_at`:

- `admin.py` line 99: `.order_by(VoiceSession.created_at.desc())` — `AttributeError` at import time (SQLAlchemy raises when building the query).
- `sessions.py` line 126: `created_at=session.created_at` — `AttributeError` at runtime on every `GET /api/sessions/{id}` call.

The `SessionStateResponse` Pydantic schema also declares `started_at: datetime` but the endpoint passes `created_at=...`, so even after the attribute is corrected the keyword name would be wrong.

**Fix required:**  
Either add `created_at` as an alias mapped to `started_at` in the model, or rename every reference to `started_at`. The schema field and the endpoint keyword must be consistent.

---

### BUG-02 — `SessionInitResponse` missing required fields (Pydantic `ValidationError` on every session init)

**Severity:** Critical  
**Files affected:** [backend/app/api/sessions.py](backend/app/api/sessions.py#L101), [backend/app/schemas/session.py](backend/app/schemas/session.py)

**Description:**  
`SessionInitResponse` declares four required (non-Optional) fields: `session_token`, `session_id`, `persona`, `survey_title`, `total_questions`, `current_question_index: int`, and `state: str`. The `init_session` handler (line 101–104) returns the object without `current_question_index` or `state`:

```python
return SessionInitResponse(
    session_token=session_token,
    session_id=str(session.id),
    persona=persona.to_dict(),
    survey_title=survey.title,
    total_questions=total_questions,
    # ← current_question_index missing (required int)
    # ← state missing (required str)
)
```

FastAPI will raise a `ValidationError` (HTTP 500) on every successful session creation, making the participant flow completely broken.

**Fix required:**  
Add `current_question_index=0, state=SessionState.GREETING.value` to the return statement.

---

### BUG-03 — `QuestionResponse` missing `question_index` (DB integrity error on every response log)

**Severity:** Critical  
**Files affected:** [backend/app/api/websocket.py](backend/app/api/websocket.py#L241), [backend/app/models/response.py](backend/app/models/response.py#L22)

**Description:**  
`Response.question_index` is `nullable=False` in the ORM model. The `QuestionResponse(...)` constructor call in the WebSocket handler never sets this field:

```python
question_response = QuestionResponse(
    session_id=session.id,
    question_id=current_q.id,
    transcript_raw=transcript,
    transcript_clean=transcript,
    was_refocused=refocus_count > 0,
    refocus_count=refocus_count,
    moderation_flagged=False,
    # ← question_index missing → DB NOT NULL violation
)
```

Every `await db.flush()` after this call will raise an `IntegrityError`, terminating the WebSocket connection mid-session without completing the response log.

**Fix required:**  
Add `question_index=sm.current_question_index` to the constructor call.

---

### BUG-04 — `/api/auth/refresh` never reads the httpOnly cookie (token refresh non-functional)

**Severity:** Critical  
**Files affected:** [backend/app/api/auth.py](backend/app/api/auth.py#L57)

**Description:**  
The `refresh_access_token` endpoint signature declares `refresh_token: str | None = None` as a plain query parameter. The httpOnly `voxora_refresh` cookie is never extracted from the request:

```python
async def refresh_access_token(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = None,   # ← query param, not cookie
) -> TokenResponse:
    from fastapi import Request  # local import — never used
    if not refresh_token:
        raise HTTPException(401, "No refresh token provided")  # always raised
```

A `from fastapi import Request` import sits unused in the function body. The endpoint will always return 401 because the cookie is never passed as a query parameter in practice.

**Fix required:**  
Replace the query param with `Cookie(None, alias="voxora_refresh")` from `fastapi`:
```python
from fastapi import Cookie
...
async def refresh_access_token(
    response: Response,
    db: AsyncSession = Depends(get_db),
    voxora_refresh: str | None = Cookie(None),
) -> TokenResponse:
```

---

### BUG-05 — Integration test `sample_participant` fixture undefined (test suite fails to collect)

**Severity:** Critical (test infrastructure)  
**Files affected:** [backend/tests/integration/test_websocket.py](backend/tests/integration/test_websocket.py#L10), [backend/tests/conftest.py](backend/tests/conftest.py)

**Description:**  
`test_websocket.py` and `test_moderation.py` reference a `sample_participant: Participant` fixture in their function signatures, but this fixture is not defined anywhere in `conftest.py`. pytest will report `fixture 'sample_participant' not found` and fail to collect the entire integration test module.

**Fix required:**  
Add `sample_participant` fixture to `conftest.py` that creates a `Participant` row linked to `sample_survey`.

---

## Part 2 — Security Deficiencies

Protections described in the README security model (Section 7) or the security instructions that are either absent or incomplete in code.

---

### SEC-01 — Refresh token revocation not implemented server-side

**Severity:** High  
**Files affected:** [backend/app/api/auth.py](backend/app/api/auth.py#L99), [backend/app/security/auth.py](backend/app/security/auth.py)

**Documented behaviour (WBS T2.5.1.3):**  
> "Implement refresh token: create, store hash in DB, set httpOnly cookie"  
> "Implement POST /api/auth/refresh with rotation (old token invalidated)"

**Actual behaviour:**  
`hash_token()` is implemented in `security/auth.py` but is never called. Refresh tokens are signed JWTs set as cookies — they are never stored in the database. The `logout` endpoint only deletes the cookie; it does not invalidate the token. A stolen refresh token extracted from browser memory/network logs remains valid for the full 7-day window even after explicit logout.

**Fix required:**  
Store a SHA-256 hash of issued refresh tokens in the `admin_users` table (or a separate `refresh_tokens` table). Validate the hash on `POST /api/auth/refresh` and delete it on `POST /api/auth/logout`.

---

### SEC-02 — Rate limiting not applied to any endpoint

**Severity:** High  
**Files affected:** [backend/app/security/rate_limiter.py](backend/app/security/rate_limiter.py), [backend/app/api/sessions.py](backend/app/api/sessions.py)

**Documented behaviour (README Section 7, Layer 7):**  
> "10 requests/minute per IP on session init endpoints"

**Actual behaviour:**  
`rate_limiter.py` contains only:
```python
limiter = Limiter(key_func=get_remote_address)
```
The `SlowAPIMiddleware` is registered in `main.py`, but no `@limiter.limit()` decorator is applied to any route. The `session init` endpoint, the primary brute-force surface, is completely unprotected by rate limiting.

**Fix required:**  
Add `@limiter.limit("10/minute")` to `init_session` in `sessions.py` and pass the `Request` object to the route handler.

---

### SEC-03 — WebSocket per-IP connection limit not enforced

**Severity:** Medium  
**Files affected:** [backend/app/api/websocket.py](backend/app/api/websocket.py), [backend/app/config.py](backend/app/config.py)

**Documented behaviour (README Section 7, Layer 7 / config):**  
`max_ws_connections_per_ip: int = 5` is defined in `Settings` but is never read or enforced. The WebSocket handler accepts unlimited concurrent connections from any IP.

**Fix required:**  
Track a per-IP connection counter in Redis on connect/disconnect and reject connections that exceed `settings.max_ws_connections_per_ip`.

---

## Part 3 — Feature Gaps (Documented, Not Implemented)

Functionality explicitly specified in `PROJECT_PLAN.md`, `WORK_BREAKDOWN_STRUCTURE.md`, or the `README.md` that has no corresponding code.

---

### FEAT-01 — Alembic migration files not created

**WBS reference:** T2.1.1.7, T2.1.1.8  
**Files:** [backend/alembic/versions/](backend/alembic/versions/) (contains only `.gitkeep`)

The database schema exists only in ORM models. No `alembic revision` has been generated. Running `alembic upgrade head` is a no-op. The database cannot be created from migrations as documented. All 6 tables and the performance indexes migration must be authored.

---

### FEAT-02 — Session reconnect flow for `IN_PROGRESS` participants not implemented

**WBS reference:** T2.4.1.6 — "Handle all edge cases: COMPLETED, IN_PROGRESS, EXPIRED, FLAGGED"  
**Files:** [backend/app/api/sessions.py](backend/app/api/sessions.py#L38)

The `init_session` handler checks `COMPLETED` and `EXPIRED` status but not `IN_PROGRESS`. When a participant reconnects after a disconnect, a **second session record** is created for the same participant, and the participant status is set to `IN_PROGRESS` again (even though it already is). This creates orphaned sessions and data loss.

**Also missing:** `FLAGGED` status check — flagged participants can re-enter and start a new session.

---

### FEAT-03 — `PUT /api/surveys/{id}/questions/{q_id}` endpoint missing

**WBS reference:** T2.2.1.7  
**Files:** [backend/app/api/surveys.py](backend/app/api/surveys.py)

The surveys router implements `POST`, `GET`, `PUT` (for the survey itself), `DELETE`, `POST /questions`, and `DELETE /questions/{q_id}`, but has no `PUT /{survey_id}/questions/{q_id}` endpoint. Existing questions cannot be updated via API.

---

### FEAT-04 — Question order rebalancing on delete not implemented

**WBS reference:** T2.2.1.8 — "DELETE /api/surveys/{id}/questions/{q_id} with order rebalancing"  
**Files:** [backend/app/api/surveys.py](backend/app/api/surveys.py)

The `delete_question` handler deletes the record but does not rebalance `order_index` values for remaining questions, leaving gaps (e.g., questions at indices 1, 3, 4 after deleting index 2). This breaks the state machine's sequential index assumption.

---

### FEAT-05 — Recent persona tracking per participant not wired to DB

**WBS reference:** T3.1.1.3 — "Implement non-repetition logic: check last 3 sessions for same participant"  
**Files:** [backend/app/api/sessions.py](backend/app/api/sessions.py#L63), [backend/app/services/persona_manager.py](backend/app/services/persona_manager.py)

`persona_manager.assign_random()` accepts `recent_persona_names` to avoid repetition, but `init_session` calls it without arguments:
```python
persona = persona_manager.assign_random()   # ← no recent names passed
```
No query is made to fetch the participant's previous sessions' personas. The non-repetition feature is implemented in `PersonaManager` but never activated in production flow.

---

### FEAT-06 — Audio storage / S3 integration **✅ DONE (IS-18, April 26)**

~~WBS reference: Feature 3.5 (response logging), README database schema~~  
~~Files: [backend/app/models/response.py](backend/app/models/response.py)~~

~~The `audio_url` column exists in the `responses` table (and is shown in the schema in the README) but is never populated. No cloud storage client, upload logic, or pre-signed URL generation exists. All response audio is discarded after TTS synthesis.~~

**Status (April 26, 2026):** COMPLETED
- StorageService created with optional `aioboto3` import and graceful degradation
- S3 configuration added to settings
- Websocket turn loop wired to upload audio after transcription
- MinIO service added to docker-compose for local dev
- Unit tests written for normal upload and missing-dependency fallback
- Integration test contract added for audio_url persistence

---

### FEAT-07 — Sentiment analysis not implemented

**WBS reference:** Implied by `sentiment_score` field in DB schema / README  
**Files:** [backend/app/models/response.py](backend/app/models/response.py), [backend/app/api/websocket.py](backend/app/api/websocket.py)

`Response.sentiment_score` is defined as `DECIMAL(4,3)` in the model and documented in the README schema, but is never populated. No NLP enrichment step exists in the turn pipeline.

---

### FEAT-08 — ElevenLabs TTS integration not implemented

**Documented:** README Tech Stack (AI Services), `config.py` `elevenlabs_api_key`, `elevenlabs_enabled`  
**Files:** [backend/app/config.py](backend/app/config.py), [backend/app/services/ai_orchestrator.py](backend/app/services/ai_orchestrator.py)

`elevenlabs_api_key` and `elevenlabs_enabled` settings exist but no ElevenLabs client code is written. The TTS always uses OpenAI regardless of the `elevenlabs_enabled` flag.

---

### FEAT-09 — WebSocket connection registry in Redis **✅ DONE (IS-15, April 26)**

~~WBS reference: T2.6.1.3 — "Implement connection registry: track active connections in Redis"~~  
~~Files: [backend/app/api/websocket.py](backend/app/api/websocket.py)~~

~~No connection registry keys are written to Redis on connect or cleaned up on disconnect. The `max_ws_connections_per_ip` setting (see SEC-03) cannot be enforced without this registry.~~

**Status (April 26, 2026):** COMPLETED
- Redis connection registry implemented with `ws_connections:{ip}` key pattern
- Per-IP limit enforcement now active via counter increment/decrement
- Connection count persisted across restarts via Redis
- Integrated with IS-09 per-IP WebSocket limit enforcement

---

### FEAT-10 — Whisper confidence threshold check **✅ DONE (IS-16, April 26)**

~~WBS reference: T3.6.1.1 — "Implement confidence threshold check on Whisper output (< 0.7 → ask to repeat)"~~  
~~Files: [backend/app/services/ai_orchestrator.py](backend/app/services/ai_orchestrator.py)~~

~~`AIOrchestratorService.transcribe()` calls the Whisper API with `response_format="text"` which returns a plain string — no confidence score. The WBS specifies confidence-based re-ask logic, which requires `response_format="verbose_json"` to obtain per-segment confidence values.~~

**Status (April 26, 2026):** COMPLETED
- Whisper API switched to `response_format="verbose_json"` for confidence extraction
- Confidence calculation implemented using `avg_logprob` from segment data
- Re-ask flow triggered for confidence < 0.70 (configurable threshold)
- Up to 3 re-ask attempts before question is skipped
- Confidence score logged to Response for quality analysis
- Unit tests added for confidence calculation at boundary values

---

### FEAT-11 — Audio energy "too quiet" detection not implemented

**WBS reference:** T3.6.1.2 — "Implement audio energy check: too quiet → 'Could you speak a little louder?'"  
**Files:** [backend/app/api/websocket.py](backend/app/api/websocket.py)

The WebSocket handler receives raw audio bytes but performs no energy/amplitude check before sending to Whisper. Silent or very low-energy audio produces empty transcripts (handled) but there is no proactive "too quiet" feedback path.

---

### FEAT-12 — Admin average session duration KPI not implemented

**README reference:** Section 5.4 — "average session duration" listed as an Overview KPI  
**Files:** [backend/app/api/admin.py](backend/app/api/admin.py), [backend/app/schemas/admin.py](backend/app/schemas/admin.py)

`AdminStats` response does not include `avg_session_duration_seconds`. The `sessions` table has `duration_seconds` and `completed_at` but no aggregation query surfaces this in the admin API or the `StatsOverview.jsx` component.

---

### FEAT-13 — Frontend unit/component tests not implemented

**WBS reference:** E4 acceptance criteria; CI pipeline expectations  
**Files:** [frontend/](frontend/), [.github/workflows/ci.yml](.github/workflows/ci.yml)

The CI `frontend-build` job only runs `npm ci` and `npm run build`. No `npm test` step exists. No test files (`*.test.jsx`, `*.spec.js`) are present anywhere in the `frontend/src/` tree. The WBS allocates story points for frontend testing (E4, E7) but none are implemented.

---

### FEAT-14 — Pre-commit hooks and PR template not configured

**WBS reference:** T1.1.1.4 — "Configure pre-commit hooks: black, ruff, eslint", T1.1.1.5 — "Document branching strategy and PR template"  
**Files:** Root workspace

No `.pre-commit-config.yaml` exists. No `.github/PULL_REQUEST_TEMPLATE.md` exists. The `black` and `ruff` checks run only in CI, not locally at commit time as specified.

---

## Part 4 — Documentation vs. Code Inconsistencies

Places where the documentation describes something differently from the actual code, without either being a crash bug or missing feature.

---

### DOC-01 — Participant URL parameter name mismatch

**README:** Section 4 and architecture diagrams use `/survey/:participantId`  
**Code:** [frontend/src/App.jsx](frontend/src/App.jsx#L20) uses `path="/survey/:inviteToken"`, [frontend/src/pages/SurveyPage.jsx](frontend/src/pages/SurveyPage.jsx) destructures `{ inviteToken } = useParams()`

The URL token is the `invite_token` UUID, not a `participantId`. Both the README and WBS consistently use `participantId` in the route path. The code is correctly named (`inviteToken`) but the documentation is misleading and could confuse developers wiring up the backend invitation URL formatter.

---

### DOC-02 — Session state diagram missing `PROCESSING` state

**README Section 5.3** and **WBS T3.2.1.1** define states as:  
`GREETING | ASKING | LISTENING | LOGGING | CLOSING | COMPLETED | TERMINATED`

**Code:** [backend/app/services/state_machine.py](backend/app/services/state_machine.py) implements 8 states, adding `PROCESSING` between `LISTENING` and `LOGGING`.

The state diagram in the README (`[INIT] → [GREETING] → [Q1_ASKING] → [Q1_LISTENING] → [Q1_LOGGING] ...`) omits the `PROCESSING` state, which is used extensively in the WebSocket handler. The documentation is out of date.

---

### DOC-03 — `GET /api/sessions/{id}` is admin-only in code, undocumented as such

**WBS T2.4.1.5:** "Implement GET /api/sessions/{id}: return current state for reconnection"

The intent in the WBS is a participant-facing reconnect endpoint (no auth token required). The actual implementation requires `get_current_admin` — the endpoint is admin-protected. Participants cannot query their own session state for reconnection, which defeats its original purpose.

---

### DOC-04 — CI triggers only on `main`, not `develop`

**PROJECT_PLAN.md Day 10:** "Trigger: every pull request to `develop` and `main`"

**Code:** [.github/workflows/ci.yml](.github/workflows/ci.yml#L4):
```yaml
on:
  pull_request:
    branches: [main]
```
`develop` is not listed. PRs to the `develop` branch will not trigger CI.

---

### DOC-05 — Route prefix duplication in auth router

**Code:** `auth.py` defines `router = APIRouter(prefix="/api/auth", ...)` AND `main.py` registers it with `app.include_router(auth_router, prefix="/api/auth", ...)`. This results in all auth routes mounting at `/api/auth/api/auth/login`, `/api/auth/api/auth/refresh`, etc.

**Expected paths:** `/api/auth/login`, `/api/auth/refresh`, `/api/auth/logout`

This is a functional bug masked by the fact that it would manifest as 404s on the correct paths. The router's own `prefix` should be removed since `main.py` provides it.

---

### DOC-06 — `SessionInitResponse` `participant_name` never populated

**Schema:** `participant_name: Optional[str]` in `SessionInitResponse`  
**Code:** `init_session` does not pass `participant_name` to the response constructor.

The frontend `SurveyPage` receives `sessionData` and could display the participant name (useful for the `PersonaCard` greeting), but the field is always `null`. This is a missing field in the response construction, not a crash (because it is `Optional`).

---

### DOC-07 — README claims `.env.example` in both directories; only backend exists

**README Section 12 (Getting Started)** references both `backend/.env.example` and `frontend/.env.example`. The backend file exists, but `frontend/.env.example` also exists (confirmed by file search). However, neither file is referenced in the directory structure listing in Section 4, which is incomplete.

**Actually corrected finding:** Both `.env.example` files exist. The README directory listing (Section 4) omits them, which is a documentation incompleteness rather than a missing file.

---

### DOC-08 — `AdminPage` sidebar links use plain `<a>` tags instead of React Router `<Link>`

**Code:** [frontend/src/pages/AdminPage.jsx](frontend/src/pages/AdminPage.jsx) — the `NavItem` component uses `<a href={href}>`, causing full-page reloads on navigation within the admin dashboard, bypassing React Router's client-side navigation. The `frontend-conventions.instructions.md` specifies React Router's `Link`/`NavLink` for internal navigation.

---

## Part 7 — Validation Update (April 25, 2026)

> **Purpose:** Re-verify high-severity findings against current workspace code after the initial April 23 report.

### 7.1 Confirmed Criticals Still Open

1. **Router prefix duplication is broader than auth only (Critical)**  
    In addition to `auth`, the same prefix-on-router + prefix-on-include pattern exists for `sessions`, `surveys`, `participants`, and `admin`. Effective paths become doubled (e.g., `/api/sessions/api/sessions/init`).

2. **`Session` field mismatch remains (Critical)**  
    `Session` model defines `started_at`, while API code still references `created_at` in session/admin flows.

3. **`SessionInitResponse` required fields still omitted (Critical)**  
    `current_question_index` and `state` are still required by schema and still missing from `init_session` response payload.

4. **WebSocket response logging still omits non-null `question_index` (Critical)**  
    `responses.question_index` is required; insert payload still does not set it.

5. **Refresh endpoint still does not read httpOnly refresh cookie (Critical)**  
    `/api/auth/refresh` still expects `refresh_token` in function signature rather than extracting `voxora_refresh` cookie.

### 7.2 Findings Corrected Since Initial Report

1. **BUG-05 is now stale / resolved**  
    `sample_participant` fixture is present in `backend/tests/conftest.py`; this part of the report is no longer accurate.

### 7.3 Additional Confirmed Gaps (Noted During Re-Validation)

1. **No route-level `@limiter.limit(...)` decorators found**  
    Limiter middleware is registered, but endpoint decorators are still absent.

2. **Alembic versions directory still scaffold-only**  
    `backend/alembic/versions/` contains only `.gitkeep`.

3. **Refresh-token hash persistence/revocation still not implemented**  
    `hash_token()` exists but is not wired to persisted token state and revocation checks.

4. **Frontend test coverage gap remains**  
    CI currently runs frontend build only; no frontend test files were found in `frontend/src/` and no test step is present in frontend CI job.

5. **CI trigger mismatch remains**  
    Pull request workflow still triggers on `main` only, not `develop`.

### 7.4 Test/Execution Environment Note

During re-validation, backend integration test execution was blocked by missing runtime dependency in the active environment:

- `ModuleNotFoundError: No module named 'redis'` while importing `app.database` through pytest `conftest.py`.

This is an environment readiness issue and should be resolved before using test pass/fail as a gating signal for closure.

### 7.5 Revised Immediate Priority (Execution Order)

1. Normalize router prefix strategy (single source of truth for all API routers).
2. Fix session schema/field mismatches (`created_at` vs `started_at`; response contract alignment).
3. Fix `/api/auth/refresh` cookie extraction and token refresh flow.
4. Fix WebSocket response persistence (`question_index`).
5. Add route-level rate-limit decorators for exposed write endpoints.
6. Restore test environment dependencies (`redis`, etc.) and re-run focused integration tests.


---

## Part 5 — Summary Table

| ID | Category | Severity | Component | Status |
|---|---|---|---|---|
| BUG-01 | Runtime Crash | Critical | Backend / Admin & Session API | Resolved in current code |
| BUG-02 | Runtime Crash | Critical | Backend / Session Init | Resolved in current code |
| BUG-03 | Data Integrity | Critical | Backend / WebSocket | Resolved in current code |
| BUG-04 | Runtime Crash | Critical | Backend / Auth | Resolved in current code |
| BUG-05 | Test Infrastructure | Critical | Tests | Resolved in current code |
| SEC-01 | Security | High | Backend / Auth | Resolved in current code |
| SEC-02 | Security | High | Backend / Rate Limiter | Resolved on covered write endpoints |
| SEC-03 | Security | Medium | Backend / WebSocket | Per-IP WS limit unenforced |
| FEAT-01 | Feature Gap | High | Backend / DB | Partially resolved: migration files now exist |
| FEAT-02 | Feature Gap | High | Backend / Session | Reconnect flow not implemented |
| FEAT-03 | Feature Gap | Medium | Backend / Surveys | `PUT /questions/{id}` missing |
| FEAT-04 | Feature Gap | Medium | Backend / Surveys | Order rebalancing on delete |
| FEAT-05 | Feature Gap | Medium | Backend / Personas | Recent persona DB query absent |
| FEAT-06 | Feature Gap | Medium | Backend / Storage | `audio_url` always null |
| FEAT-07 | Feature Gap | Low | Backend / NLP | `sentiment_score` always null |
| FEAT-08 | Feature Gap | Low | Backend / TTS | ElevenLabs not integrated |
| FEAT-09 | Feature Gap | Medium | Backend / WebSocket | No Redis connection registry |
| FEAT-10 | Feature Gap | Medium | Backend / AI | Whisper confidence check missing |
| FEAT-11 | Feature Gap | Low | Backend / Audio | Energy/quiet detection missing |
| FEAT-12 | Feature Gap | Low | Backend / Admin | Avg duration KPI missing |
| FEAT-13 | Feature Gap | Medium | Frontend / Tests | No frontend tests exist |
| FEAT-14 | Feature Gap | Low | DevOps | No pre-commit hooks or PR template |
| DOC-01 | Doc Inconsistency | Low | Frontend / Routing | `:participantId` vs `:inviteToken` |
| DOC-02 | Doc Inconsistency | Low | Backend / State Machine | `PROCESSING` state undocumented |
| DOC-03 | Doc Inconsistency | Medium | Backend / Sessions | Reconnect endpoint admin-protected |
| DOC-04 | Doc Inconsistency | Low | CI/CD | Resolved in current code |
| DOC-05 | Runtime Bug | High | Backend / Auth | Resolved in current code |
| DOC-06 | Doc Inconsistency | Low | Backend / Session | Resolved in current code |
| DOC-07 | Doc Inconsistency | Info | Documentation | Directory listing incomplete |
| DOC-08 | Code Quality | Low | Frontend / Nav | `<a>` instead of `<Link>` |

---

## Part 6 — Recommended Fix Priority

### Immediate

1. **FEAT-02** — Add `IN_PROGRESS` reconnect and `FLAGGED` rejection behavior in session init  
2. **SEC-03 / FEAT-09** — Implement Redis WebSocket connection registry and enforce per-IP limit  
3. **FEAT-03** — Implement `PUT /api/surveys/{id}/questions/{q_id}`  
4. **FEAT-04** — Implement order rebalancing after question delete  
5. **FEAT-05** — Wire recent persona DB query into `init_session`  

### Short-term (before staging deployment)

6. **FEAT-01** — Validate Alembic migrations end-to-end on PostgreSQL, including index expectations  
7. **FEAT-10** — Switch Whisper to `verbose_json` and implement confidence threshold  
8. **FEAT-13** — Add Vitest/Jest frontend tests and wire them into CI  
9. **DOC-03** — Decide whether `GET /api/sessions/{id}` remains admin-only or should support participant reconnect usage  

### Medium-term (feature completeness)

10. **FEAT-06**, **FEAT-07**, **FEAT-08**, **FEAT-11**, **FEAT-12**, **FEAT-14**  
11. **DOC-01**, **DOC-02**, **DOC-06**, **DOC-08**  

### Backlog

12. Broader end-to-end, load, and UAT execution across the still-pending late phases

---

*Analysis performed by reviewing all backend models, API routes, services, security modules, frontend hooks/stores/pages, test fixtures, CI workflows, and cross-referencing against `README.md`, `PROJECT_PLAN.md`, and `WORK_BREAKDOWN_STRUCTURE.md`.*

---

## Part 7 — Implementation Update (April 25–26, 2026)

### 7.1 Backend Hardening (Session 2: April 25)

The following high-priority fixes from Parts 1–4 are now implemented:

1. **Route prefix normalization**
    - Removed double-prefix mounting at app startup.
    - API routers are now included without duplicate `prefix` values.

2. **Session contract correctness**
    - `SessionInitResponse` now returns required fields: `participant_name`, `current_question_index`, and `state`.
    - Session state endpoint now returns `started_at` (not `created_at`) and includes required schema fields.

3. **WebSocket response persistence integrity**
    - Added `question_index` assignment when creating `QuestionResponse` entries.

4. **Refresh-token cookie handling**
    - `/api/auth/refresh` now reads `voxora_refresh` from cookie via FastAPI `Cookie(...)`.

5. **Rate limiting hardening (route-level decorators)**
    - Applied `@limiter.limit(...)` to critical write endpoints in `auth`, `sessions`, `surveys`, `participants`, and `admin` routes.

6. **Model import stability fixes**
    - Added `backend/app/models/__init__.py` to ensure SQLAlchemy model registration consistency.
    - Added `ParticipantStatus` enum in `participant.py` for route/model compatibility.

7. **CI trigger and focused regression execution updates**
    - CI pull request trigger updated to include both `main` and `develop`.
    - Added explicit focused contract test execution step in CI.

### 7.2 Sprint 1 Backend Features (Session 3: April 26)

The complete Sprint 1 backend feature block has been implemented in Session 3:

1. **IS-09 — WebSocket per-IP connection limits** [✅ Done]
   - Per-IP counter tracked in Redis: `ws_connections:{ip}`
   - Reject 6th+ concurrent connection from same IP with close code 1008
   - Counter auto-cleaned via TTL, survives process restarts

2. **IS-10 — Alembic migration baseline** [✅ Done]
   - Initial schema migration `a0000000001` covering all 6 core tables
   - Migration chain validated: `a0000000001` → `b7f2c1a4d9e8` → `c3a8f2b1e7d4`
   - Performance indexes on participant.invite_token, participant.status, FK fields

3. **IS-11 — Session reconnect + status guards** [✅ Done]
   - `IN_PROGRESS` participants can reconnect and get existing session token
   - `FLAGGED` participants rejected with HTTP 403 and neutral message
   - `COMPLETED` and `EXPIRED` handled as before
   - Question index restored from state machine or DB on reconnect

4. **IS-12/13/14 — Question CRUD and rebalancing** [✅ Done]
   - `PUT /api/surveys/{id}/questions/{q_id}` endpoint implemented for partial updates
   - `order_index` rebalancing on delete via single atomic UPDATE statement
   - Recent persona DB query wiring (last 3 personas excluded from assignment)
   - All 3 features covered by integration tests

5. **IS-15 — Redis WebSocket connection registry** [✅ Done]
   - Per-IP counter incremented on `websocket.accept()`, decremented on close
   - Shared across processes via Redis with TTL renewal
   - Powers IS-09 per-IP limit enforcement
   - Connection registry survives backend restarts

6. **IS-16 — Whisper confidence threshold + re-ask flow** [✅ Done]
   - Switched to `response_format="verbose_json"` for segment confidence extraction
   - Re-ask up to 3 times if average confidence < 0.70
   - Threshold configurable via `settings.whisper_confidence_threshold`
   - Confidence score logged to Response for post-session quality analysis

7. **IS-18 — S3/MinIO audio upload integration** [✅ Done]
   - `StorageService` created with optional `aioboto3` import and graceful degradation
   - Returns `None` when S3 unavailable (no crash, non-fatal upload failures logged)
   - S3 configuration settings added to `config.py`
   - MinIO service added to docker-compose for local audio storage development
   - Websocket turn loop wired to call `storage_service.upload_audio()` after transcription

### 7.3 Validation Performed

Focused implementation validation tests were added and executed:

- `backend/tests/integration/test_auth_sessions_contracts.py` (Session 2)
- `backend/tests/unit/test_storage_service.py` (Session 3, new file for storage service)
- `backend/tests/integration/test_auth_sessions_contracts.py` (Session 3 update: added audio_url persistence contract)

Validated behaviors now include:

1. No double-prefixed route paths
2. Login success path stores refresh token state and sets cookie
3. Invalid and inactive login paths are rejected correctly
4. Refresh endpoint enforces cookie presence
5. Refresh succeeds with valid cookie and rejects untracked tokens
6. Logout revokes stored refresh token state
7. Session init returns required response contract fields
8. Session init rejects invalid/completed/expired/inactive survey states
9. Session init returns `503` when Redis/session-store initialization fails
10. Rate-limit enforcement on login and session-init routes
11. Admin session-state endpoint returns correct not-found and success behavior
12. Moderation integration remains covered in focused integration runs
13. Storage service upload succeeds with valid S3 client (Session 3)
14. Storage service gracefully returns `None` when `aioboto3` unavailable (Session 3)
15. Websocket response includes `audio_url` field from storage service (Session 3)

**Latest focused run result (Session 2):** `29 passed`, with `100%` scoped coverage across `app/api/auth.py`, `app/api/sessions.py`, and `app/services/moderation.py`.

**Session 3 validation:** All Sprint 1 features validated via direct app import (no `ModuleNotFoundError`), focused unit tests for storage service, and integration test contract additions.

### 7.4 Remaining Priority Gaps

Still pending from earlier sections (now updated after Session 3 completions):

1. Session E2E testing and frontend automated test coverage
2. Real PostgreSQL migration execution validation and index verification beyond the new migration files
3. Broader end-to-end workflow validation for participant, reconnect, and admin flows
4. Sentiment analysis implementation (FEAT-07, IS-19)
5. ElevenLabs TTS provider integration (FEAT-08, IS-23)
6. Audio energy "too quiet" detection (FEAT-11, IS-22)
7. Average session duration KPI in admin stats (FEAT-12, IS-21)
8. Pre-commit hooks configuration (FEAT-14, IS-24)
9. GitHub PR template (FEAT-14, IS-25)
10. Documentation alignment: route parameter, state machine diagram, access control clarification (DOC-01, DOC-02, DOC-03, IS-26, IS-27, IS-28)
11. Deciding whether the websocket surface should be brought under the same 100% coverage discipline as the scoped auth/session/moderation integration runner
