# VoxOra — MVP-First Approach

> **Created:** April 25, 2026  
> **Owner:** Tech Lead  
> **Strategy:** Resolve all open issues against the existing scaffolding before introducing new features. Ship a working, tested, deployable MVP before expanding scope.

---

## Related Documents

| Document | Purpose |
|---|---|
| [PROJECT_PLAN.md](PROJECT_PLAN.md) | Phase-wise roadmap, sprint durations, and overall completion status |
| [ISSUE_TRACKER.md](ISSUE_TRACKER.md) | Per-issue breakdown with acceptance criteria, tasks, and current status |
| [IMPLEMENTATION_GAP_ANALYSIS.md](IMPLEMENTATION_GAP_ANALYSIS.md) | Root-cause analysis of every gap found between code and documentation |
| [WORK_BREAKDOWN_STRUCTURE.md](WORK_BREAKDOWN_STRUCTURE.md) | Epic/feature/story/task decomposition with story-point estimates |
| [Session_1.md](Session_1.md) | Session 1 work log — initial scaffolding and structure |
| [Session_2.md](Session_2.md) | Session 2 work log — auth hardening, refresh-token persistence, 100% scoped coverage |

---

## What "MVP" Means for VoxOra

The MVP is the simplest complete participant journey that can be demonstrated end-to-end:

```
Participant opens survey link
  → POST /api/sessions/init         (session created, participant greeted)
  → WebSocket /ws/session/{id}      (voice exchange — questions asked, answers captured)
  → Session closes                  (state = COMPLETED, responses saved to DB)
  → Admin logs in                   (POST /api/auth/login)
  → Admin views results             (GET /api/admin/stats, GET /api/admin/sessions)
```

Everything needed for this single path to work, reliably, on a fresh environment — that is the MVP gate.

---

## Current State Summary

All phases have been scaffolded and committed to `master`. The code files exist. However several paths within that code are either incomplete, missing edge-case handling, or not yet validated against a live environment. See [PROJECT_PLAN.md — Current Status](PROJECT_PLAN.md#current-status--april-2026) for the per-phase breakdown.

| Phase | Scaffolded | Production Ready | Blocking MVP |
|---|---|---|---|
| 0 — Foundation | ✅ | ✅ | No |
| 1 — Backend Core & DB | ✅ | ❌ | **Yes** — reconnect, question CRUD, Alembic |
| 2 — AI Orchestration | ✅ | ⚠️ Partial | No (happy-path works) |
| 3 — Frontend Participant | ✅ | ⚠️ Partial | No (happy-path works) |
| 4 — Security Hardening | ✅ | ❌ | **Yes** — WebSocket connection limit open |
| 5 — Admin Dashboard | ✅ | ⚠️ Partial | No (basic views work) |
| 6 — Integration & E2E | 🟡 Started | ❌ | **Yes** — full E2E suite not run |
| 7 — Performance | ❌ | ❌ | No (post-MVP) |
| 8 — Deployment & DevOps | ✅ | ⚠️ Partial | No (Docker files exist, not live-validated) |
| 9 — UAT & Launch | ❌ | ❌ | No (post-MVP) |

---

## Open Issues Mapped to MVP Impact

Full issue details are in [ISSUE_TRACKER.md](ISSUE_TRACKER.md). The table below maps each open issue to its MVP impact.

| Issue | Title | MVP Impact | Sprint |
|---|---|---|---|
| **IS-11** | Session reconnect + flagged participant guard | 🔥 Blocks MVP — duplicate sessions on reconnect; flagged users can re-enter | Sprint 1 |
| **IS-10** | Full initial-schema Alembic migration | 🔥 Blocks MVP — no tables without migration; fresh deploy crashes | Sprint 1 |
| **IS-09** | Per-IP WebSocket connection limit (Redis) | 🔥 Blocks MVP — critical security gap on the primary voice endpoint | Sprint 1 |
| **IS-12** | `PUT /api/surveys/{id}/questions/{q_id}` | ⚠️ Needed for MVP — admins cannot correct questions after creation | Sprint 1 |
| **IS-13** | Question order rebalancing on delete | ⚠️ Needed for MVP — deleting a question breaks the state machine index | Sprint 1 |
| **IS-14** | Recent-persona DB wiring | 🟡 Nice-to-have — quality improvement; does not block happy path | Sprint 1 |
| **IS-29/T2** | PersonaCard renders `participant_name` | 🟡 Nice-to-have — UX polish; greeting still works without it | Sprint 2 |
| **IS-30** | Replace `<a>` with `<NavLink>` in admin sidebar | 🟡 Polish — no functional blocker | Sprint 2 |
| **IS-21** | Avg session duration KPI on admin stats | 🟡 Polish — admin can still see results without it | Sprint 2 |
| **IS-17** | Frontend unit/component tests | ⚠️ Quality gate before UAT | Sprint 2 |
| **IS-15** | Redis WebSocket connection registry | 🔵 Post-MVP enhancement | Backlog |
| **IS-16** | Whisper confidence threshold re-ask | 🔵 Post-MVP enhancement | Backlog |
| **IS-18** | Audio storage (S3/object store) | 🔵 Post-MVP enhancement | Backlog |
| **IS-19** | Sentiment analysis on responses | 🔵 Post-MVP enhancement | Backlog |
| **IS-22** | Audio energy "too quiet" detection | 🔵 Post-MVP enhancement | Backlog |

---

## Sprint Plan

### Sprint 1 — Backend Correctness Gate

**Goal:** Every endpoint on the critical participant path works correctly on a freshly deployed environment with no workarounds.

**Reference issues:** IS-11, IS-10, IS-09, IS-12, IS-13, IS-14  
**Reference WBS epics:** [E2 — Backend API & Database](WORK_BREAKDOWN_STRUCTURE.md), [E5 — Security Hardening](WORK_BREAKDOWN_STRUCTURE.md)  
**Reference gap analysis:** [Part 2 — Security Deficiencies](IMPLEMENTATION_GAP_ANALYSIS.md), [Part 3 — Feature Gaps](IMPLEMENTATION_GAP_ANALYSIS.md)

#### Tasks in priority order

1. **IS-10** — Generate and validate full initial-schema Alembic migration  
   - Run `alembic revision --autogenerate -m "initial_schema"` and verify all 6 tables + constraints + indexes  
   - Test `upgrade head` + `downgrade -1` against a real PostgreSQL instance  
   - _Definition of done:_ `docker compose up` on a blank machine creates all tables without error

2. **IS-11** — Session reconnect and flagged participant guard  
   - `IN_PROGRESS` participant → return existing session token (no new session)  
   - `FLAGGED` participant → HTTP 403 neutral message  
   - `COMPLETED/EXPIRED` → existing 409/410 responses (already present)  
   - _Definition of done:_ 4 integration tests pass (one per status edge case)

3. **IS-09** — Per-IP WebSocket connection limit  
   - Redis `INCR/DECR ws_connections:{ip}` counter; reject at `settings.max_ws_connections_per_ip`  
   - _Definition of done:_ unit test confirms 6th connection is rejected with close code 1008

4. **IS-12** — Survey question update endpoint  
   - `PUT /api/surveys/{id}/questions/{q_id}` with partial update, 404/403 guards, admin auth  
   - _Definition of done:_ endpoint appears in Swagger UI, 4 unit tests pass

5. **IS-13** — Question order rebalancing on delete  
   - Single atomic `UPDATE … SET order_index = order_index - 1 WHERE order_index > :deleted_index`  
   - _Definition of done:_ integration test verifies contiguous indices after deletion

6. **IS-14** — Recent-persona DB wiring  
   - Query last-3 sessions for participant, pass persona names to `assign_random()`  
   - _Definition of done:_ unit test confirms correct argument passed with mocked prior sessions

**Sprint 1 exit criteria:**  
- `alembic upgrade head` succeeds on a blank PostgreSQL instance  
- All 6 issues above have passing tests  
- Existing 29-test integration suite still passes at 100% scoped coverage  
- No regressions in unit test suite (69 tests)

---

### Sprint 2 — Frontend Polish + Quality Gates

**Goal:** Admin dashboard is complete for MVP use, participant UI is polished, frontend has test coverage.

**Reference issues:** IS-29/T2, IS-30, IS-21, IS-17  
**Reference WBS epics:** [E4 — Frontend Participant Experience](WORK_BREAKDOWN_STRUCTURE.md), [E6 — Admin Dashboard](WORK_BREAKDOWN_STRUCTURE.md), [E7 — Integration & Testing](WORK_BREAKDOWN_STRUCTURE.md)

#### Tasks in priority order

1. **IS-17** — Frontend unit and component tests  
   - React Testing Library tests for `useVoiceSession`, `useAdminAuth` hooks  
   - Component tests for `PersonaCard`, `VoiceRecorder`, `SessionSummary`

2. **IS-21** — Average session duration KPI on admin stats  
   - Backend: `func.avg(VoiceSession.duration_seconds)` in `/api/admin/stats`  
   - Frontend: KPI card in `StatsOverview.jsx`

3. **IS-29/T2** — PersonaCard renders `participant_name`  
   - Verify `PersonaCard.jsx` reads `sessionData.participant_name` (backend T1 already done in Session 2)

4. **IS-30** — Replace `<a>` with `<NavLink>` in admin sidebar  
   - `AdminPage.jsx` NavItem component refactor

**Sprint 2 exit criteria:**  
- Frontend test coverage ≥ 80% on hooks and key components  
- Admin stats endpoint returns `avg_session_duration_seconds`  
- No full-page reloads on admin navigation

---

### Post-MVP Backlog

These issues are deferred until after the first live participant run. They improve the product but do not block the MVP happy path.

| Issue | Title | Rationale for Deferral |
|---|---|---|
| IS-15 | Redis WebSocket connection registry | Per-IP limit (IS-09) is sufficient for MVP; full registry is an enhancement |
| IS-16 | Whisper confidence threshold re-ask | Happy path works; this improves transcript quality under adverse conditions |
| IS-18 | Audio storage (S3/object store) | Audio is processed in memory for MVP; archival can come after first live run |
| IS-19 | Sentiment analysis on responses | Value-add analytics; not needed for basic result visibility |
| IS-22 | Audio energy "too quiet" detection | UX enhancement; normal-volume users are unaffected |

See [ISSUE_TRACKER.md — M4/M5 sections](ISSUE_TRACKER.md) for full acceptance criteria on these items.

---

## MVP Definition of Done

The MVP is complete when all of the following are true:

- [ ] `alembic upgrade head` creates all tables on a blank PostgreSQL 16 instance
- [ ] `docker compose up` starts all services without errors
- [ ] A participant can open a survey link and complete a voice session end-to-end
- [ ] Session responses are saved to the database with correct `question_index` values
- [ ] Admin can log in, view session list, view individual response transcripts
- [ ] All 6 Sprint 1 issues are closed with passing tests
- [ ] Existing 29 integration + 69 unit tests continue to pass
- [ ] No Critical or High severity open issues remain in [ISSUE_TRACKER.md](ISSUE_TRACKER.md)

---

## What Is Explicitly Out of Scope for MVP

The following items from the project plan are **not** required for the MVP gate and will be addressed in subsequent iterations:

- Phase 7 — Performance Optimization (latency tuning, streaming, caching)
- Phase 9 — UAT & Production Launch (beta cohort, go-live runbook, handover docs)
- IS-15 through IS-19, IS-22 (enhancement features listed in Post-MVP Backlog above)
- Audio archival / S3 storage
- Sentiment analysis dashboard

See [PROJECT_PLAN.md — Phase 7 and Phase 9](PROJECT_PLAN.md) for the full scope of those phases.
