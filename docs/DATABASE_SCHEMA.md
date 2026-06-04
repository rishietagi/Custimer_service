# Relational Database Schema

The backend uses a local SQLite database file `customer_service.db` managed by the SQLAlchemy ORM.

---

## 1. Database Model Diagrams

```mermaid
erDiagram
    users ||--o{ products : owns
    users ||--o{ orders : places
    users ||--o{ appointments : books
    users ||--o{ support_cases : files
    users ||--o{ chat_sessions : conducts

    users {
        string user_id PK
        string username UNIQUE
        string password_hash
        string full_name
        string email
        string phone
        string address
        string city
        string pincode
    }

    products {
        string product_id PK
        string user_id FK
        string category
        string model_number
        string serial_number
        string purchase_date
        string warranty_status
        string installation_date
    }

    orders {
        string order_id PK
        string user_id FK
        string product_name
        string status
        string registered_phone
        string registered_email
        string created_at
    }

    appointments {
        string appointment_id PK
        string user_id FK
        string customer_name
        string product_category
        string product_model
        string serial_number
        string purchase_date
        string warranty_status
        string issue_description
        string address
        string city
        string pincode
        string preferred_date
        string preferred_time_slot
        string status
        string technician_name
        string created_at
    }

    support_cases {
        string case_id PK
        string user_id FK
        string title
        string description
        string status
        string category
        string created_at
    }

    chat_sessions {
        string session_id PK
        string user_id FK
        string current_state
        string chat_data
        string state_history
        string messages
        string updated_at
    }
```

---

## 2. Table Specifications

### Users Table (`users`)
Stores user login credentials (SHA-256 hashed) and default site visitation addresses.
* **user_id** (TEXT, PK): Unique identifier.
* **username** (TEXT, UNIQUE): Case-insensitive.
* **password_hash** (TEXT): SHA-256 string.
* **full_name** (TEXT)
* **email** (TEXT)
* **phone** (TEXT)
* **address** (TEXT, Nullable)
* **city** (TEXT, Nullable)
* **pincode** (TEXT, Nullable)

### Products Table (`products`)
Stores appliances registered by user accounts.
* **product_id** (TEXT, PK)
* **user_id** (TEXT, FK references `users.user_id` ON DELETE CASCADE)
* **category** (TEXT)
* **model_number** (TEXT)
* **serial_number** (TEXT)
* **purchase_date** (TEXT)
* **warranty_status** (TEXT)
* **installation_date** (TEXT, Nullable)

### Orders Table (`orders`)
Mock orders for shipping tracking.
* **order_id** (TEXT, PK)
* **user_id** (TEXT, FK references `users.user_id` ON DELETE CASCADE)
* **product_name** (TEXT)
* **status** (TEXT): `Delivered`, `Shipped`, `Delayed`, `Installation Pending`.
* **registered_phone** (TEXT)
* **registered_email** (TEXT)
* **created_at** (TEXT)

### Appointments Table (`appointments`)
Service appointments booked for home visits.
* **appointment_id** (TEXT, PK)
* **user_id** (TEXT, FK references `users.user_id` ON DELETE CASCADE)
* **customer_name** (TEXT)
* **product_category** (TEXT)
* **product_model** (TEXT)
* **serial_number** (TEXT)
* **purchase_date** (TEXT)
* **warranty_status** (TEXT)
* **issue_description** (TEXT)
* **address** (TEXT)
* **city** (TEXT)
* **pincode** (TEXT)
* **preferred_date** (TEXT)
* **preferred_time_slot** (TEXT)
* **status** (TEXT): `Scheduled`, `Rescheduled`, `Cancelled`, `Completed`.
* **technician_name** (TEXT, Nullable)
* **created_at** (TEXT)

### Support Cases Table (`support_cases`)
Billing, AMC, cancellation, or escalated complaint tickets.
* **case_id** (TEXT, PK)
* **user_id** (TEXT, FK references `users.user_id` ON DELETE CASCADE)
* **title** (TEXT)
* **description** (TEXT)
* **status** (TEXT): `Open`, `Resolved`.
* **category** (TEXT)
* **created_at** (TEXT)

### Chat Sessions Table (`chat_sessions`)
Stores active FSM chat history.
* **session_id** (TEXT, PK): Unique chat session UUID.
* **user_id** (TEXT, FK references `users.user_id` ON DELETE CASCADE)
* **current_state** (TEXT): Active node in FSM (e.g. `HOME_MENU`).
* **chat_data** (TEXT): Stringified JSON object storing diagnostic state variables.
* **state_history** (TEXT): Stringified JSON list of previous states (for stack undos).
* **messages** (TEXT): Stringified JSON list of chat bubbles history.
* **updated_at** (TEXT)
