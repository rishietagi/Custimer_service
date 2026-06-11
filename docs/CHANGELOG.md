# Changelog

All notable changes to this project will be documented in this file. This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] - 2026-06-10
### Added
- Voice-First "Call Center Agent" tab simulating a real customer support phone call experience.
- Automated start/end call routines, duration timers, and visual connection status badges.
- Real-time client-side live transcription using browser webkitSpeechRecognition.
- Continuous listening mode with configurable silence detection (auto-submit) and manual Push-to-Talk mode.
- Speaker volume slider, voice mute/unmute toggles, and audio replay controls.
- Automatic FSM step tracking, appointment booking summaries, and final structured LLM call summaries.
- Relational SQLite table `call_sessions` linked to users and appointments.

## [1.1.0] - 2026-06-05
### Added
- Voice-First pipeline converting user spoken commands into text and playing spoken replies.
- Built-in integration with Groq Whisper Large v3 for speech-to-text transcription.
- Built-in integration with Groq canopylabs/orpheus-v1-english for text-to-speech voice responses.
- Resilient client-side fallback using browser native **Web Speech API (`window.speechSynthesis`)** to speak responses when backend TTS is unavailable, rate-limited, or requires terms acceptance.
- Decoupled state machine parser using Groq Llama 3.3 for hybrid natural language understanding (NLU).
- Deterministic regex-based fallback system if Groq APIs are rate-limited or unavailable.
- Real-time voice interruption capability on the client, stopping assistant voice output when a user starts speaking/typing.
- Microphone permission error handling, visual status logs (Listening, Transcribing, Thinking, Speaking, Error/Retry), and animated waveforms.

## [1.0.0] - 2026-06-10
### Added
- Decoupled client-server architecture using a FastAPI ASGI server and a React + Vite + TypeScript client app.
- Interactive, responsive dashboard featuring scheduled visit reminders, active support tickets, and recent shipping orders summaries.
- Advanced guided diagnostic FSM chat assistant with sliding bubbles, avatar icons, micro-animations, and context-dependent form integrations.
- Complete OpenAPI integration with Uvicorn. Swagger docs hosted at `/docs`.
- SQLite database migrations configured using SQLAlchemy model mappings.
- Auto-documentation validation script `scripts/update_docs.py` to synchronize files and keep reports fresh.

### Changed
- Refactored Streamlit pages into dedicated TypeScript React pages (`Login`, `Dashboard`, `ChatAssistant`, `Appointments`, `Orders`, `Profile`).
- Migrated custom inline CSS styles into clean Tailwind utility classes and tailwind theme configuration files.
- Ported input validation logic (email formatting, date validations, pincode/phone checks) to backend core functions.

---

## [0.1.0] - 2026-05-10
### Added
- Initial proof of concept (POC) for Guided Customer Support.
- Build system using Streamlit widgets.
- Simple file-based SQLite database with plain SQL helper functions.
- Raw guided FSM chatbot troubleshooting steps.
