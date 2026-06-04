# Project Report: Streamlit to FastAPI + React Migration

---

## 1. Project Overview
This project presents the architectural migration and complete front-end/back-end refactoring of the **SmartCare Customer Support Portal**. The application has been upgraded from a single-file Streamlit prototype to a modern, decoupled web application.

## 2. Business Problem
Prototypes built with frameworks like Streamlit lack visual customizability, layout responsiveness, and session separation. For enterprise stakeholder reviews, a portal must demonstrate premium customer journeys, handle concurrent API requests, validate input schemas strictly, and align with design standards of global consumer appliance brands like SmartCare, Samsung, and Apple.

## 3. Objectives
* **Decoupled Architecture:** Isolate presentation logic (React client) from business validation logic (FastAPI server).
* **Guided Diagnostic Chat FSM:** Implement a robust state-machine chat flow with undos, button choices, and inline form rendering.
* **Premium UX/UI:** Style the client using custom Tailwind design tokens matching Signature branding (signature reds, clean spacing, glassmorphic hover details, skeletal loaders).
* **Robust Persistence:** Model entities using SQLAlchemy ORM over a relational SQLite database.

## 4. User Personas
* **Persona A: David (Homeowner):** Needs a fast diagnostic assistant to book a washing machine repair under warranty. Prefers mobile support without reading dense manuals.
* **Persona B: Sarah (Service Manager):** Needs to review, reschedule, or cancel technician appointments booked online.

## 5. Functional Requirements
* Guided troubleshooting chat state transitions.
* User authentication (sign-in, registration, demo user bypass).
* Appliance details registration.
* Shipment timelines lookups.
* Appointment scheduling, cancellations, and reschedules.
* Raise escalated ticket cases.

## 6. Non-Functional Requirements
* Responsive layout (desktop sidebar, mobile drawer navbar).
* Auto-generated API documentation (Swagger UI).
* Micro-animations (Framer Motion transitions, bouncing typing dots).
* Local file database persistence (SQLite).

## 7. User Journeys
1. **Diagnosis & Booking:** Sign in $\rightarrow$ Select Product Help in Chat $\rightarrow$ Input category/model/serial $\rightarrow$ Fill service site address $\rightarrow$ Choose preferred date/slot $\rightarrow$ Appointment confirmed.
2. **Order Check & Complaint:** Search order by ID + Phone $\rightarrow$ Read status timeline $\rightarrow$ Click &ldquo;Raise Complaint&rdquo; $\rightarrow$ Ticket submitted.

## 8. System Architecture
Uses a decoupled React client and FastAPI server, communicating via REST JSON endpoints. Database queries are abstracted through SQLAlchemy models.

## 9. Database Design
Comprises six tables: `users`, `products`, `orders`, `appointments`, `support_cases`, and `chat_sessions`. Refer to [DATABASE_SCHEMA.md](file:///c:/Users/rishi/Desktop/customer_service_chatbot/docs/DATABASE_SCHEMA.md) for details.

## 10. API Design
Exposes REST routes under `/api/v1` for authentication, user dashboard aggregates, order tracking, appointment actions, and chat session state machine operations. Refer to [API_DOCUMENTATION.md](file:///c:/Users/rishi/Desktop/customer_service_chatbot/docs/API_DOCUMENTATION.md).

## 11. Frontend Design
Styled in dark-charcoal (#1e1e1e) and SmartCare signature red (#a50034) with clear typography (Outfit/Inter). The client is structured into modular pages:
* **Login:** Sign in and registration with credentials advice panel.
* **Dashboard:** Home screen displaying scheduled visits, shipped orders, and ticket logs.
* **ChatAssistant:** guided diagnostic conversational flow with progress and undo keys.
* **Appointments:** Service visitation card list with cancel/reschedule forms.
* **Orders:** Purchase logistics timelines with complaint forms.
* **Profile:** Account options, registered devices lists, and active ticket timelines.

## 12. Chat Flow Logic
Driven by a backend state machine class `ChatFSM` in `backend/app/services/chat_service.py` that checks input, transitions state tags, saves history, and writes DB records on terminal nodes.

## 13. Appointment Workflow
Allows users to rescheduling preferred dates/slots or cancelling visist. Both operations update fields inside `appointments` table and trigger react state updates.

## 14. Future Enhancements
* Live agent handoff via WebSockets.
* OCR integration (scanning serial number plates from phone cameras).
* LLM integration for unguided natural language fallback.

## 15. Assumptions
* User runs application locally (localhost).
* SQLite is sufficient for single-user POC storage.
* Passwords are encrypted with SHA-256 (sufficient for POC credential validations).

## 16. Limitations
* SQLite lacks concurrent multi-write safety in distributed clouds.
* Mock technicians assigned deterministically based on product categories.

## 17. Deployment Strategy
* **Backend:** Deploy as Docker container in AWS ECS.
* **Frontend:** Build static files (`npm run build`) and host on AWS S3/CloudFront CDN.

## 18. Testing Strategy
* **API Testing:** Automated pytest tests for auth and FSM API endpoints.
* **UI Testing:** Manual verification of chat dialogues and form inputs.

## 19. Screenshots Section
*(Screenshots can be added in mock media layouts or captured during walkthroughs)*
* **Mock Layout: Login Page tabbed widgets**
* **Mock Layout: Diagnostic Assistant Chat Window**
* **Mock Layout: Service Appointment dashboard logs**

## 20. Conclusion
This migration demonstrates how Streamlit prototypes can be successfully refactored into modular, production-grade applications that satisfy enterprise security, performance, and aesthetic standards.
