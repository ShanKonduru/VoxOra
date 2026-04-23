from __future__ import annotations

import asyncio
import io
import logging
from typing import AsyncGenerator

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class AIOrchestratorService:
    """
    Core AI orchestration service.
    Handles: transcription (STT) → response generation → speech synthesis (TTS).
    """

    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    # ── Speech-to-Text ────────────────────────────────────────────────────────

    async def transcribe(self, audio_bytes: bytes, language: str = "en") -> str:
        """Transcribe audio bytes using OpenAI Whisper."""
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.webm"
        response = await self._client.audio.transcriptions.create(
            model=settings.openai_stt_model,
            file=audio_file,
            language=language,
            response_format="text",
        )
        return str(response).strip()

    # ── Response Generation ───────────────────────────────────────────────────

    async def generate_response(
        self, system_prompt: str, user_transcript: str
    ) -> str:
        """Generate AI response using GPT-4o with the sandwiched system prompt."""
        for attempt in range(3):
            try:
                completion = await self._client.chat.completions.create(
                    model=settings.openai_chat_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_transcript},
                    ],
                    max_tokens=300,
                    temperature=0.4,
                )
                return completion.choices[0].message.content or ""
            except Exception as exc:
                if attempt == 2:
                    logger.error("generate_response failed after 3 attempts: %s", exc)
                    return (
                        "I'm sorry, I'm experiencing a brief technical difficulty. "
                        "Could you please repeat that?"
                    )
                await asyncio.sleep(1.5 * (attempt + 1))
        return ""

    # ── Text-to-Speech ────────────────────────────────────────────────────────

    async def synthesize_speech(self, text: str, voice_id: str = "nova") -> bytes:
        """Synthesize full speech audio and return as bytes (mp3)."""
        response = await self._client.audio.speech.create(
            model=settings.openai_tts_model,
            voice=voice_id,  # type: ignore[arg-type]
            input=text,
            response_format="mp3",
        )
        return response.read()

    async def synthesize_speech_stream(
        self, text: str, voice_id: str = "nova"
    ) -> AsyncGenerator[bytes, None]:
        """Stream TTS audio chunks for low-latency playback."""
        async with self._client.audio.speech.with_streaming_response.create(
            model=settings.openai_tts_model,
            voice=voice_id,  # type: ignore[arg-type]
            input=text,
            response_format="mp3",
        ) as response:
            async for chunk in response.iter_bytes(chunk_size=4096):
                yield chunk

    # ── Full Orchestrated Turn ────────────────────────────────────────────────

    async def run_turn(
        self,
        audio_bytes: bytes,
        system_prompt: str,
        voice_id: str = "nova",
    ) -> tuple[str, bytes]:
        """
        Execute a complete conversational turn:
        1. Transcribe participant audio
        2. Generate AI text response
        3. Synthesize AI speech
        Returns (transcript, audio_bytes)
        """
        transcript = await self.transcribe(audio_bytes)
        response_text = await self.generate_response(system_prompt, transcript)
        audio_response = await self.synthesize_speech(response_text, voice_id)
        return transcript, audio_response


orchestrator_service = AIOrchestratorService()
