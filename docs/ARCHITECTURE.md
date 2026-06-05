# System Architecture

This document describes the architectural layout, component interactions, and Guided FSM state machine transitions.

---

## 1. Architectural Overview

The portal uses a decoupled **client-server** architecture.

```mermaid
graph TD
    Client[React Frontend <br> Port 3000] <-->|JSON REST APIs <br> Axios| Server[FastAPI Backend <br> Port 8000]
    Server <-->|SQLAlchemy ORM| DB[(SQLite Database <br> customer_service.db)]
```

* **Frontend Client:** Built using React + TypeScript, bundled with Vite. Styled with Tailwind CSS, utilizing Framer Motion for micro-animations and smooth layout transitions. Runs on port 3000.
* **Backend Server:** Built using FastAPI, served via Uvicorn. Validates payloads using Pydantic schemas. Runs on port 8000.
* **Database Layer:** A local SQLite relational database storing user records, registrations, appointments, tickets, and active chat logs.

---

## 2. Guided Support FSM (Finite State Machine)

The chatbot diagnostic journey acts as a state machine where each user input transitions the session to a new node, culminating in service appointments or tickets.

```mermaid
stateDiagram-v2
    [*] --> HOME_MENU
    
    state HOME_MENU {
        [*] --> A_Product_Help
        [*] --> B_Order_Status
        [*] --> C_Other_Help
    }

    HOME_MENU --> PRODUCT_CATEGORY : Option A
    HOME_MENU --> ORDER_LOOKUP : Option B
    HOME_MENU --> OTHER_HELP_MENU : Option C

    state Path_A_Product_Repair {
        PRODUCT_CATEGORY --> PRODUCT_MODEL
        PRODUCT_MODEL --> PRODUCT_PURCHASE_DATE
        PRODUCT_PURCHASE_DATE --> PRODUCT_WARRANTY
        PRODUCT_WARRANTY --> PRODUCT_SERIAL
        PRODUCT_SERIAL --> PRODUCT_INSTALL_DATE
        PRODUCT_INSTALL_DATE --> ISSUE_COLLECTION
        ISSUE_COLLECTION --> CONFIRM_DETAILS_BEFORE_BOOKING
        CONFIRM_DETAILS_BEFORE_BOOKING --> SERVICE_ADDRESS : Yes
        CONFIRM_DETAILS_BEFORE_BOOKING --> HOME_MENU : No
        SERVICE_ADDRESS --> SERVICE_SCHEDULE
        SERVICE_SCHEDULE --> BOOKING_CONFIRMATION : DB Write (Appointment)
    }

    state Path_B_Order_Tracking {
        ORDER_LOOKUP --> ORDER_STATUS_DISPLAY : Match Found
        ORDER_STATUS_DISPLAY --> ORDER_COMPLAINT_FORM : Raise Complaint
        ORDER_COMPLAINT_FORM --> TICKET_SUBMITTED : DB Write (Support Case)
        ORDER_STATUS_DISPLAY --> ORDER_CALLBACK_CONFIRM : Request Callback
        ORDER_STATUS_DISPLAY --> ORDER_ESCALATE_CONFIRM : Escalate Ticket
    }

    state Path_C_Other_Services {
        OTHER_HELP_MENU --> OTHER_WARRANTY_INFO : AMC Quote
        OTHER_HELP_MENU --> OTHER_PROD_REGISTRATION : Register Device
        OTHER_HELP_MENU --> OTHER_INSTALL_REQUEST : Request Setup
        OTHER_HELP_MENU --> OTHER_BILL_HELP : Billing Query
        OTHER_HELP_MENU --> OTHER_CANCEL_RETURN : Return Order
        OTHER_HELP_MENU --> OTHER_FEEDBACK : Rate Portal
        OTHER_HELP_MENU --> OTHER_COMPLAINT : General Complaint
        OTHER_HELP_MENU --> OTHER_FAQ : Read Accordion

        OTHER_WARRANTY_INFO --> TICKET_SUBMITTED
        OTHER_PROD_REGISTRATION --> TICKET_SUBMITTED : DB Write (Product)
        OTHER_INSTALL_REQUEST --> TICKET_SUBMITTED : DB Write (Appointment)
        OTHER_BILL_HELP --> TICKET_SUBMITTED
        OTHER_CANCEL_RETURN --> TICKET_SUBMITTED
        OTHER_FEEDBACK --> TICKET_SUBMITTED
        OTHER_COMPLAINT --> TICKET_SUBMITTED
    }

    BOOKING_CONFIRMATION --> HOME_MENU : Restart
    TICKET_SUBMITTED --> HOME_MENU : Restart
```
* **Step Back Navigation:** Pushing previous state tags onto `state_history` lets users revert transitions by popping state tags and restoring previous chat data.

---

## 3. Voice Pipeline Sequence

The voice dialogue features follow a sequential, decoupled pipeline:

```mermaid
sequenceDiagram
    autonumber
    actor User as Customer
    participant FE as React Frontend (Vite)
    participant BE as FastAPI Backend (Uvicorn)
    participant WS as Whisper Large v3 (Groq)
    participant LLM as Llama 3.3/3.1 NLU & Stylist (Groq)
    participant FSM as Chat FSM Engine
    participant TTS as Canopy Labs Orpheus (Groq)

    User->>FE: Speaks command
    FE->>FE: Records audio stream (WebM Blob)
    FE->>BE: Uploads audio file via Multipart POST /voice
    BE->>WS: Sends raw audio bytes
    WS-->>BE: Returns transcribed text
    BE->>BE: Sanitizes transcript
    BE->>LLM: Parses user intent (NLU mapping)
    LLM-->>BE: Returns structured FSM input (or clarification)
    BE->>FSM: Executes FSM transition logic
    FSM->>FSM: Commits state data / registers DB entries
    FSM-->>BE: Returns next state prompt
    BE->>LLM: Restyles prompt into natural conversational spoken reply
    LLM-->>BE: Returns natural spoken response string
    BE->>TTS: Submits spoken reply string
    TTS-->>BE: Returns raw WAV audio bytes
    BE-->>FE: Returns ChatSessionResponse (JSON) + audio base64 + transcript text
    FE->>User: Displays text transcript & updates active form components
    FE->>User: Plays voice response audio (HTML5 Audio player or falls back to Web Speech synthesis)
```

* **Interruption Handling:** The frontend monitors user actions (microphone clicks, keyboard typing) and instantly stops active HTML5 audio playback (or browser SpeechSynthesis) to ensure smooth, natural pacing.
* **Deterministic Fallback:** If Groq services fail or rate-limit requests, the backend falls back to local regex-based parsing rules and standard text responses.
* **SpeechSynthesis Fallback (Client-Side):** If the backend TTS generation fails (e.g. because terms need to be accepted on Groq Console, rate limits, or connectivity errors) or the generated audio file fails to load/play in the browser, the frontend automatically falls back to speaking the bot's reply using the browser's native **Web Speech API (`window.speechSynthesis`)**. This provides full resilience and robust client-side voice replies.
