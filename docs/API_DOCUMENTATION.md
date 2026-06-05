# API Documentation

The SmartCare backend services expose REST APIs prefixed under `/api/v1`. The interactive Swagger documentation is hosted at the root endpoint (`/docs`).

---

## 1. Authentication Service (`/auth`)

### Sign In
* **Endpoint:** `POST /api/v1/auth/login`
* **Request Schema (JSON):**
  ```json
  {
    "username": "customer1",
    "password": "password123"
  }
  ```
* **Response Schema (UserResponse):**
  ```json
  {
    "user_id": "usr_john1",
    "username": "customer1",
    "full_name": "John Doe",
    "email": "john.doe@support-example.com",
    "phone": "5550199283",
    "address": "123 Maple Avenue, Apt 4B",
    "city": "Chicago",
    "pincode": "60601"
  }
  ```

### Account Registration
* **Endpoint:** `POST /api/v1/auth/register`
* **Request Schema (UserCreate):**
  ```json
  {
    "username": "newuser",
    "password": "secretpassword",
    "full_name": "New User Name",
    "email": "user@example.com",
    "phone": "5550123456",
    "address": "789 Pine Rd",
    "city": "Dallas",
    "pincode": "75201"
  }
  ```
* **Response:** `UserResponse` (returns user profile on success).

---

## 2. Profile & Products Service (`/users`)

### Retrieve Profile & Dashboard Statistics
* **Endpoint:** `GET /api/v1/users/{user_id}/dashboard`
* **Response Schema:**
  ```json
  {
    "user": { ...UserResponse },
    "products": [ ...ProductResponse ],
    "appointments": [ ...AppointmentResponse ],
    "orders": [ ...OrderResponse ],
    "support_cases": [ ...SupportCaseResponse ]
  }
  ```

### Register Appliance
* **Endpoint:** `POST /api/v1/users/{user_id}/products`
* **Request Schema:**
  ```json
  {
    "category": "Refrigerator",
    "model_number": "LFXS26973S",
    "serial_number": "REF987654321",
    "purchase_date": "2024-05-15",
    "warranty_status": "In Warranty",
    "installation_date": "2024-05-16"
  }
  ```
* **Response:** `ProductResponse`

---

## 3. Order Management Service (`/orders`)

### General Order Lookup
* **Endpoint:** `GET /api/v1/orders/lookup`
* **Query Parameters:**
  * `order_id`: string (e.g. `ORD-1153`)
  * `contact_info`: string (e.g. `jane.smith@support-example.com` or `5550188722`)
* **Response:** `OrderResponse`

### Request Call Back
* **Endpoint:** `POST /api/v1/orders/{order_id}/callback`
* **Query Parameters:** `user_id`

### Escalate Order Issue
* **Endpoint:** `POST /api/v1/orders/{order_id}/escalate`
* **Query Parameters:** `user_id`
* **Response:** `SupportCaseResponse`

### Submit Order Complaint
* **Endpoint:** `POST /api/v1/orders/{order_id}/complaint`
* **Query Parameters:** `user_id`
* **Request Body:** `{ "title": "...", "description": "...", "category": "..." }`

---

## 4. Service Appointments Service (`/appointments`)

### Get User Appointments
* **Endpoint:** `GET /api/v1/appointments/user/{user_id}`
* **Response:** `List[AppointmentResponse]`

### Reschedule Service Booking
* **Endpoint:** `PUT /api/v1/appointments/{appointment_id}/reschedule`
* **Request Body (AppointmentReschedule):**
  ```json
  {
    "preferred_date": "2026-06-15",
    "preferred_time_slot": "12:00 PM - 03:00 PM (Afternoon)"
  }
  ```

### Cancel Service Booking
* **Endpoint:** `PUT /api/v1/appointments/{appointment_id}/cancel`

---

## 5. Support Cases Service (`/support-cases`)

### Get User Support Tickets
* **Endpoint:** `GET /api/v1/support-cases/user/{user_id}`
* **Response:** `List[SupportCaseResponse]`

### Create General Ticket
* **Endpoint:** `POST /api/v1/support-cases`
* **Query Parameters:**
  * `user_id`: string (e.g. `usr_john1`)
* **Request Body (SupportCaseCreate):**
  ```json
  {
    "title": "Double Charged Invoice",
    "description": "Charged twice for television order ORD-9021",
    "category": "Bill / invoice help",
    "status": "Open"
  }
  ```
* **Response:** `SupportCaseResponse`

---

## 6. Guided Chat Session Service (`/chat`)

### Schema Additions: `ChatSessionResponse`
The chat session response schema includes optional voice and transcription fields to support voice pipelines without bloating the database:
- `audio`: `string | null` (base64-encoded WAV voice stream of the assistant's reply)
- `transcript`: `string | null` (transcribed user text, populated for voice messages)

### Initialize Session
* **Endpoint:** `POST /api/v1/chat/session`
* **Query Parameters:** `user_id`
* **Response:** `ChatSessionResponse` (populates `audio` with the greeting speech)

### Post Chat Input / Response
* **Endpoint:** `POST /api/v1/chat/session/{session_id}/message`
* **Request Schema (ChatMessagePost):**
  ```json
  {
    "input_value": "Refrigerator",
    "user_display_str": "Category Selection: Refrigerator"
  }
  ```
* **Response:** `ChatSessionResponse` (returns updated FSM state, data, message logs, and `audio` response)

### Post Voice Input / Response
* **Endpoint:** `POST /api/v1/chat/session/{session_id}/voice`
* **Request Format:** `multipart/form-data`
* **Form Fields:**
  * `file`: `UploadFile` (audio recording blob, e.g., webm, ogg, or wav)
* **Response:** `ChatSessionResponse` (returns FSM state, message logs, user `transcript` transcription, and assistant `audio` reply)

### Undo last step (Go Back)
* **Endpoint:** `POST /api/v1/chat/session/{session_id}/back`
* **Response:** `ChatSessionResponse`

### Restart Chat Flow
* **Endpoint:** `POST /api/v1/chat/session/{session_id}/restart`
* **Response:** `ChatSessionResponse`
