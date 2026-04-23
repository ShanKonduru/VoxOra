# Voxora Project Instructions & Architecture Guardrails

This document serves as the primary context for the development of Voxora. All generated code must adhere to the standards and logic defined herein.

## 1. Project Mission
Voxora is an AI-powered, voice-first survey platform that conducts formal, high-quality interviews. The goal is to collect structured feedback through a personalized, interactive agent experience while maintaining strict professional boundaries.

## 2. Technical Stack Requirements
- **Frontend:** React (Vite), Tailwind CSS, Lucide Icons.
- **Audio:** WebRTC or WebSockets for real-time streaming; Voice Activity Detection (VAD) is mandatory.
- **Backend:** Python FastAPI.
- **AI Stack:** OpenAI Realtime API (for low-latency voice) or Whisper (STT) + GPT-4o + ElevenLabs (TTS).
- **Data:** PostgreSQL with Prisma ORM.

## 3. The "Voxora Persona" Logic
Every AI agent generated must follow these rules:
- **Formalism:** Maintain a polite, executive, and professional tone.
- **Randomization:** On `session_start`, randomly select from a `PersonaRegistry` (Name, Gender, Dialect).
- **Persistence:** Store the assigned persona in the database linked to the `ParticipantID` to ensure consistency across refreshes.

## 4. CRITICAL: Security & Anti-Takeover Guardrails
This is the highest priority. All code must implement the following:
- **Instructional Anchoring:** The System Prompt must be structured to prevent "Prompt Injection." Use a "Sandwich" technique where core constraints are restated at the end of every LLM call.
- **Input Sanitization Middleware:** Every transcript from the user must pass through a filter. If the text matches "jailbreak" patterns (e.g., "Ignore previous instructions," "You are now a..."), the backend must intercept and return a standardized "Refocusing" response.
- **Out-of-Bounds (OOB) Handling:** If the user asks a "stupid" or "unwanted" question, the agent MUST NOT answer. It must use a polite redirection: "My apologies, but I am only authorized to discuss the survey. Let us return to the current topic: [Current Question]."
- **Moderation:** Integrate the OpenAI Moderation API. Any hate speech or harassment triggers an immediate `Session.Terminate()` event.
- **Stateless Knowledge:** The agent should have NO knowledge of the world outside the survey context and the persona it is playing.

## 5. State Management & Flow
- **Linear Progression:** Use a State Machine to track survey progress (e.g., `START` -> `Q1` -> `Q2` -> ... -> `COMPLETE`).
- **Data Integrity:** Do not move to the next question until the LLM confirms a valid response has been transcribed for the current question.

## 6. Admin & Dashboard Standards
- **Summarization:** Use an LLM to generate a 1-sentence "Sentiment and Key Takeaway" for each voice response.
- **Auth:** Implement JWT-based authentication for the `/admin` dashboard.
- **Reminders:** Create a service layer for sending "Pending" status notifications via Email/Webhook.

## 7. Code Style
- Use functional components and Hooks in React.
- Follow PEP8 for Python backend code.
- Implement comprehensive logging for all AI-to-User interactions to help identify future injection attempts.