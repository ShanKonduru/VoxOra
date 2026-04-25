from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, WebSocketException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, get_redis
from app.models.participant import ParticipantStatus
from app.models.question import Question
from app.models.response import Response as QuestionResponse
from app.models.session import Session as VoiceSession
from app.models.survey import Survey
from app.prompts.refocus_templates import (
    MAX_REFOCUS_BEFORE_SKIP,
    get_refocus_phrase,
    get_repeat_request,
    get_skip_message,
)
from app.prompts.voxora_interviewer import PromptBuilder
from app.security.auth import decode_token
from app.security.input_sanitizer import input_sanitizer
from app.services.ai_orchestrator import orchestrator_service
from app.services.moderation import moderation_service
from app.services.state_machine import SESSION_STATE_TTL, SessionState, SurveyStateMachine
from app.config import settings as _settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])

_MSG_AUDIO = "audio"
_MSG_CONTROL = "control"

_WS_CONN_KEY = "ws_connections:{ip}"
_WS_CONN_TTL_SECONDS = SESSION_STATE_TTL + 60


def _extract_client_ip(websocket: WebSocket) -> str:
    """Resolve client IP from proxy headers first, then socket metadata."""
    forwarded_for = websocket.headers.get("x-forwarded-for", "")
    if forwarded_for:
        first_hop = forwarded_for.split(",", 1)[0].strip()
        if first_hop:
            return first_hop

    if websocket.client and websocket.client.host:
        return websocket.client.host

    return "unknown"


async def _acquire_ws_slot(ip: str) -> tuple[bool, object]:
    """Increment per-IP counter. Returns (allowed, redis). Caller must release on disconnect."""
    try:
        redis = await get_redis()
        key = _WS_CONN_KEY.format(ip=ip)
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, _WS_CONN_TTL_SECONDS)
        if count > _settings.max_ws_connections_per_ip:
            await redis.decr(key)
            return False, redis
        return True, redis
    except Exception:
        # Redis unavailable — fail open to avoid blocking all connections
        return True, None  # pragma: no cover


async def _release_ws_slot(redis: object, ip: str) -> None:
    """Decrement per-IP counter, floor at 0."""
    if redis is None:
        return  # pragma: no cover
    try:
        key = _WS_CONN_KEY.format(ip=ip)
        current = await redis.get(key)
        if current and int(current) > 0:
            await redis.decr(key)
    except Exception:
        pass  # pragma: no cover


def _build_control(event: str, data: dict[str, Any] | None = None) -> str:
    return json.dumps({"type": "control", "event": event, **(data or {})})


async def _load_session(
    db: AsyncSession, session_id: uuid.UUID
) -> tuple[VoiceSession, Survey, list[Question]] | None:
    result = await db.execute(
        select(VoiceSession).where(VoiceSession.id == session_id)
    )
    session: VoiceSession | None = result.scalar_one_or_none()
    if not session:
        return None
    survey_result = await db.execute(select(Survey).where(Survey.id == session.participant.survey_id))
    survey: Survey | None = survey_result.scalar_one_or_none()
    if not survey:
        return None
    questions = sorted(survey.questions, key=lambda q: q.order_index)
    return session, survey, questions


@router.websocket("/session/{session_id}")
async def voice_session_ws(websocket: WebSocket, session_id: uuid.UUID) -> None:
    await websocket.accept()

    client_ip = _extract_client_ip(websocket)
    allowed, ws_redis = await _acquire_ws_slot(client_ip)
    if not allowed:
        await websocket.close(code=1008)
        return

    try:
        # ── Authenticate via session token in first text message ─────────────────
        try:
            auth_msg = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
            auth_data = json.loads(auth_msg)
            token = auth_data.get("session_token", "")
            payload = decode_token(token, expected_type="access")
            token_session_id = payload.get("sub", "")
            if token_session_id != str(session_id):
                await websocket.close(code=4001)
                return
        except Exception:
            await websocket.close(code=4001)
            return

        async with AsyncSessionLocal() as db:
            from sqlalchemy.orm import selectinload

            full_session_q = await db.execute(
                select(VoiceSession)
                .options(
                    selectinload(VoiceSession.participant).selectinload("survey").selectinload("questions")
                )
                .where(VoiceSession.id == session_id)
            )
            session = full_session_q.scalar_one_or_none()
            if not session:
                await websocket.close(code=4004)
                return

            survey: Survey = session.participant.survey
            questions: list[Question] = sorted(survey.questions, key=lambda q: q.order_index)

            redis = await get_redis()
            sm = await SurveyStateMachine.load(session_id, redis)
            if not sm:
                sm = SurveyStateMachine(
                    session_id=session_id,
                    total_questions=len(questions),
                    current_state=SessionState(session.state),
                    current_question_index=session.current_question_index,
                )

            from app.services.persona_manager import Persona
            persona = Persona.from_dict(session.persona)

            # Send greeting
            greeting_text = PromptBuilder.build_greeting(
                persona=persona,
                participant_name=session.participant.name,
                survey_title=survey.title,
            )
            greeting_audio = await orchestrator_service.synthesize_speech(
                greeting_text, voice_id=persona.voice_id
            )
            await websocket.send_bytes(greeting_audio)
            await websocket.send_text(_build_control("question", {
                "question_index": sm.current_question_index,
                "question_text": questions[sm.current_question_index].question_text,
                "total": len(questions),
            }))

            sm.transition(SessionState.ASKING)
            await sm.save(redis)

            refocus_count = 0

            try:
                while not sm.is_terminal():
                    data = await websocket.receive()
                    msg_type = data.get("type")

                    # ── Handle binary audio frame ─────────────────────────────────
                    if msg_type == "websocket.receive" and data.get("bytes"):
                        audio_bytes: bytes = data["bytes"]
                        sm.transition(SessionState.LISTENING)
                        await sm.save(redis)
                        sm.transition(SessionState.PROCESSING)
                        await sm.save(redis)

                        # 1. Transcribe
                        try:
                            transcript = await orchestrator_service.transcribe(audio_bytes)
                        except Exception as exc:
                            logger.warning("STT failed: %s", exc)
                            repeat_audio = await orchestrator_service.synthesize_speech(
                                get_repeat_request(), voice_id=persona.voice_id
                            )
                            await websocket.send_bytes(repeat_audio)
                            sm.transition(SessionState.ASKING)
                            await sm.save(redis)
                            continue

                        if not transcript.strip():
                            repeat_audio = await orchestrator_service.synthesize_speech(
                                get_repeat_request(), voice_id=persona.voice_id
                            )
                            await websocket.send_bytes(repeat_audio)
                            sm.transition(SessionState.ASKING)
                            await sm.save(redis)
                            continue

                        # 2. Sanitize
                        san = input_sanitizer.check(transcript)
                        if not san.is_safe:
                            refocus_count += 1
                            current_q = questions[sm.current_question_index]
                            if refocus_count >= MAX_REFOCUS_BEFORE_SKIP:
                                refocus_count = 0
                                skip_audio = await orchestrator_service.synthesize_speech(
                                    get_skip_message(), voice_id=persona.voice_id
                                )
                                await websocket.send_bytes(skip_audio)
                                has_more = sm.skip_question()
                                await sm.save(redis)
                                if not has_more:
                                    break
                                await websocket.send_text(_build_control("question", {
                                    "question_index": sm.current_question_index,
                                    "question_text": questions[sm.current_question_index].question_text,
                                    "total": len(questions),
                                }))
                            else:
                                brief = current_q.question_text[:80]
                                refocus_audio = await orchestrator_service.synthesize_speech(
                                    get_refocus_phrase(brief), voice_id=persona.voice_id
                                )
                                await websocket.send_bytes(refocus_audio)
                                sm.transition(SessionState.ASKING)
                                await sm.save(redis)
                            continue

                        # 3. Moderate
                        mod_result = await moderation_service.check(transcript)
                        if mod_result.is_flagged:
                            session.is_flagged = True
                            session.flag_reason = f"Moderation: {mod_result.flagged_categories}"
                            sm.terminate("moderation_flag")
                            await sm.save(redis)
                            terminate_audio = await orchestrator_service.synthesize_speech(
                                "I appreciate your time, but I must end this session now. Thank you.",
                                voice_id=persona.voice_id,
                            )
                            await websocket.send_bytes(terminate_audio)
                            await websocket.send_text(_build_control("terminated"))
                            await db.commit()
                            break

                        # 4. Generate AI response
                        current_q = questions[sm.current_question_index]
                        system_prompt = PromptBuilder.build(
                            persona=persona,
                            survey_title=survey.title,
                            question_text=current_q.question_text,
                            current_index=sm.current_question_index,
                            total_questions=len(questions),
                            participant_name=session.participant.name,
                            follow_up_text=current_q.follow_up_text,
                        )
                        ai_text = await orchestrator_service.generate_response(
                            system_prompt=system_prompt,
                            user_transcript=transcript,
                        )

                        # 5. Log response
                        sm.transition(SessionState.LOGGING)
                        await sm.save(redis)

                        question_response = QuestionResponse(
                            session_id=session.id,
                            question_id=current_q.id,
                            question_index=sm.current_question_index,
                            transcript_raw=transcript,
                            transcript_clean=transcript,
                            was_refocused=refocus_count > 0,
                            refocus_count=refocus_count,
                            moderation_flagged=False,
                        )
                        db.add(question_response)
                        await db.flush()

                        # 6. Synthesize and stream AI response
                        ai_audio = await orchestrator_service.synthesize_speech(
                            ai_text, voice_id=persona.voice_id
                        )
                        await websocket.send_bytes(ai_audio)

                        refocus_count = 0

                        # 7. Advance state machine
                        has_more = sm.advance()
                        session.current_question_index = sm.current_question_index
                        session.state = sm.current_state.value
                        await db.commit()
                        await sm.save(redis)

                        if not has_more:
                            # Deliver closing message
                            closing = PromptBuilder.build_closing(
                                persona=persona,
                                participant_name=session.participant.name,
                            )
                            closing_audio = await orchestrator_service.synthesize_speech(
                                closing, voice_id=persona.voice_id
                            )
                            await websocket.send_bytes(closing_audio)
                            sm.transition(SessionState.COMPLETED)
                            session.state = SessionState.COMPLETED.value
                            session.participant.status = ParticipantStatus.COMPLETED
                            await db.commit()
                            await sm.save(redis)
                            await websocket.send_text(_build_control("completed"))
                            break
                        else:
                            await websocket.send_text(_build_control("question", {
                                "question_index": sm.current_question_index,
                                "question_text": questions[sm.current_question_index].question_text,
                                "total": len(questions),
                            }))

                    elif msg_type == "websocket.receive" and data.get("text"):
                        # Control message from client
                        ctrl = json.loads(data["text"])
                        if ctrl.get("event") == "ping":
                            await websocket.send_text(_build_control("pong"))

            except WebSocketDisconnect:
                logger.info("WebSocket disconnected: session_id=%s", session_id)
                session.state = sm.current_state.value
                await db.commit()
            except Exception as exc:
                logger.exception("WebSocket error for session %s: %s", session_id, exc)
                try:
                    await websocket.close(code=1011)
                except Exception:
                    pass
    finally:
        await _release_ws_slot(ws_redis, client_ip)
