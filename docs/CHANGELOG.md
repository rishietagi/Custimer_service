# Changelog

All notable changes to this project will be documented in this file. This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-06-04
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
