# SmartCare - Home Appliance Customer Service Portal

This repository contains a modern, production-grade Customer Service Support Portal built using a decoupled **React + Vite** frontend client and a **FastAPI** backend server with an ORM-managed **SQLite** database.

The portal models a complete self-service support journey: registering appliances, querying orders with interactive timeline progress graphs, running a guided state-machine chatbot to diagnose problems, and scheduling/managing technician home repair visits.

---

## 📁 Project Structure

```text
customer_service_chatbot/
│
├── backend/                # FastAPI ASGI application
│   ├── app/
│   │   ├── api/            # Combined API router registry
│   │   ├── core/           # Configuration settings and field validators
│   │   ├── database/       # SQLAlchemy engine & session configurations
│   │   ├── models/         # SQLAlchemy database entity tables
│   │   ├── schemas/        # Pydantic request/response validation schemas
│   │   ├── services/       # Chat FSM transition logic and actions
│   │   ├── routers/        # Endpoint routers (auth, users, orders, chat, etc.)
│   │   └── main.py         # App initialization & database seeding
│   ├── environment.yml     # Conda environment dependency registry
│   └── run.py              # Server run script
│
├── frontend/               # React Vite client application
│   ├── src/
│   │   ├── assets/         # Global brand styling and variables
│   │   ├── components/     # Navbars, Sidebars, Timelines, and Skeletons
│   │   ├── pages/          # Login, Dashboard, ChatAssistant, Appointments, Orders, Profile
│   │   └── services/       # Axios API client integrations
│   ├── package.json        # npm package registry
│   ├── tailwind.config.js  # Tailwind CSS theme customization
│   └── vite.config.ts      # Vite dev server and proxy rules
│
├── docs/                   # Dedicated project reports and specifications
│   ├── PROJECT_REPORT.md   # Product overview & functional journeys
│   ├── TECH_STACK.md       # Technical evaluation & considerations
│   ├── API_DOCUMENTATION.md# REST API specs
│   ├── DATABASE_SCHEMA.md  # Relational ERDs & table formats
│   ├── CHANGELOG.md        # Release version history
│   └── ARCHITECTURE.md     # Flowcharts & state machine diagrams
│
└── scripts/
    ├── update_docs.py      # Auto-documentation synchronization script
    └── remove_lg.py        # Brand name cleaning script
```

---

## 🛠️ Setup Instructions

### 1. Backend Setup & Run
Create and activate the Conda environment, then start the FastAPI Uvicorn server:

```bash
# Navigate to project root
conda env create -f backend/environment.yml
conda activate appliance-support

# Run the FastAPI server
uvicorn backend.app.main:app --port 8000 --reload
```
* **API Swagger Specifications:** [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Frontend Setup & Run
The React client dependencies are installed and run inside the same conda environment:

```bash
# Navigate to frontend folder
cd frontend

# Install package dependencies
npm install

# Start Vite dev server
npm run dev
```
* **Web App URL:** [http://localhost:3000](http://localhost:3000)

*(Vite is configured to automatically proxy all client `/api` requests to the backend server running on port 8000).*

---

## 🔑 Demo Access Credentials

The database will be initialized automatically and seeded with sample accounts on first run:

| Username | Password | Profile Owner | Key Data Included |
| :--- | :--- | :--- | :--- |
| `customer1` | `password123` | **John Doe** | Refrigerator & Washer, 1 Pending Order, 1 Scheduled Visit |
| `customer2` | `password123` | **Jane Smith** | Dishwasher, 2 Orders (Delayed/Pending), 1 Scheduled Visit |

> [!TIP]
> You can also register a brand new user using the **Create Account** tab on the login screen.

---

## 💡 Core Features Included

1. **Aggregated Dashboard:** Displays upcoming visit summaries, shipping progress blocks, and ticket logs.
2. **Guided FSM Chatbot:** Runs a progressive state-machine (troubleshoots categories, model shortcuts, serial checks) that hooks into scheduling forms to book technician visits.
3. **Timeline Logistics:** Serves order lookup indexes detailing shipping stages (Confirmed, Shipped, Delivered, Pending).
4. **Visits Planner:** Expanding panels for inspections, inline date rescheduling forms, and cancellation confirmations.
5. **Auto-Documentation Script:** Runs validations to check consistency between code files and markdown documents.
