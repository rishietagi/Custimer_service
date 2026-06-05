import hashlib
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os

from backend.app.core.config import settings
from backend.app.database.session import engine, SessionLocal
from backend.app.database.base import Base

# Import models to ensure they are registered on Base
from backend.app.models.user import User
from backend.app.models.product import Product
from backend.app.models.order import Order
from backend.app.models.appointment import Appointment
from backend.app.models.support_case import SupportCase

from backend.app.api.api_v1 import api_router

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Modern Customer Support API for SmartCare Portal",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount Static Files for audio/reference files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # backend/app
STATIC_DIR = os.path.join(os.path.dirname(BASE_DIR), "static")  # backend/static
os.makedirs(os.path.join(STATIC_DIR, "audio"), exist_ok=True)
app.mount("/api/static", StaticFiles(directory=STATIC_DIR), name="static")

# Set CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def seed_database():
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        if user_count > 0:
            return  # already seeded
            
        # 1. Create Users
        user1_id = "usr_john1"
        user1 = User(
            user_id=user1_id,
            username="customer1",
            password_hash=hash_password("password123"),
            full_name="John Doe",
            email="john.doe@support-example.com",
            phone="5550199283",
            address="123 Maple Avenue, Apt 4B",
            city="Chicago",
            pincode="60601"
        )
        
        user2_id = "usr_jane2"
        user2 = User(
            user_id=user2_id,
            username="customer2",
            password_hash=hash_password("password123"),
            full_name="Jane Smith",
            email="jane.smith@support-example.com",
            phone="5550188722",
            address="456 Oak Boulevard",
            city="Austin",
            pincode="78701"
        )
        db.add(user1)
        db.add(user2)
        db.flush() # flush to get foreign keys working

        # 2. Add Products
        p1 = Product(
            product_id="prod_ref1",
            user_id=user1_id,
            category="Refrigerator",
            model_number="LFXS26973S",
            serial_number="REF987654321",
            purchase_date=(date.today() - timedelta(days=500)).isoformat(),
            warranty_status="In Warranty",
            installation_date=(date.today() - timedelta(days=495)).isoformat()
        )
        p2 = Product(
            product_id="prod_wash1",
            user_id=user1_id,
            category="Washing Machine",
            model_number="WM4000HBA",
            serial_number="WASH11223344",
            purchase_date=(date.today() - timedelta(days=200)).isoformat(),
            warranty_status="In Warranty",
            installation_date=(date.today() - timedelta(days=198)).isoformat()
        )
        p3 = Product(
            product_id="prod_dish1",
            user_id=user2_id,
            category="Dishwasher",
            model_number="LDT7819BD",
            serial_number="DISH88776655",
            purchase_date=(date.today() - timedelta(days=800)).isoformat(),
            warranty_status="Out of Warranty",
            installation_date=(date.today() - timedelta(days=795)).isoformat()
        )
        db.add_all([p1, p2, p3])

        # 3. Add Orders
        o1 = Order(
            order_id="ORD-9021",
            user_id=user1_id,
            product_name="OLED C3 55-inch TV",
            status="Delivered",
            registered_phone="5550199283",
            registered_email="john.doe@support-example.com",
            created_at=(datetime.now() - timedelta(days=10)).isoformat()
        )
        o2 = Order(
            order_id="ORD-4482",
            user_id=user1_id,
            product_name="NeoChef Countertop Microwave",
            status="Shipped",
            registered_phone="5550199283",
            registered_email="john.doe@support-example.com",
            created_at=(datetime.now() - timedelta(days=2)).isoformat()
        )
        o3 = Order(
            order_id="ORD-1153",
            user_id=user2_id,
            product_name="SmartCare Smart Wi-Fi Front Control Dryer",
            status="Delayed",
            registered_phone="5550188722",
            registered_email="jane.smith@support-example.com",
            created_at=(datetime.now() - timedelta(days=5)).isoformat()
        )
        o4 = Order(
            order_id="ORD-5531",
            user_id=user2_id,
            product_name="QuadWash Pro Dishwasher",
            status="Installation Pending",
            registered_phone="5550188722",
            registered_email="jane.smith@support-example.com",
            created_at=(datetime.now() - timedelta(days=1)).isoformat()
        )
        db.add_all([o1, o2, o3, o4])

        # 4. Add Appointments
        apt1 = Appointment(
            appointment_id="APT-REF-101",
            user_id=user1_id,
            customer_name="John Doe",
            product_category="Refrigerator",
            product_model="LFXS26973S",
            serial_number="REF987654321",
            purchase_date=(date.today() - timedelta(days=500)).isoformat(),
            warranty_status="In Warranty",
            issue_description="Warming up and door seal loose",
            address="123 Maple Avenue, Apt 4B",
            city="Chicago",
            pincode="60601",
            preferred_date=(date.today() + timedelta(days=3)).isoformat(),
            preferred_time_slot="09:00 AM - 12:00 PM (Morning)",
            status="Scheduled",
            technician_name="Sarah Miller (Ref Expert)",
            created_at=datetime.utcnow().isoformat()
        )
        apt2 = Appointment(
            appointment_id="APT-DISH-202",
            user_id=user2_id,
            customer_name="Jane Smith",
            product_category="Dishwasher",
            product_model="LDT7819BD",
            serial_number="DISH88776655",
            purchase_date=(date.today() - timedelta(days=800)).isoformat(),
            warranty_status="Out of Warranty",
            issue_description="Loud grinding noise during wash cycle",
            address="456 Oak Boulevard",
            city="Austin",
            pincode="78701",
            preferred_date=(date.today() + timedelta(days=5)).isoformat(),
            preferred_time_slot="12:00 PM - 03:00 PM (Afternoon)",
            status="Scheduled",
            technician_name="David Chen (Appliance Specialist)",
            created_at=datetime.utcnow().isoformat()
        )
        db.add_all([apt1, apt2])

        # 5. Add Support Cases
        sc1 = SupportCase(
            case_id="CAS-BILL-99",
            user_id=user1_id,
            title="Double Charged Invoice",
            description="I was charged twice on my credit card for the OLED TV purchase. Order ORD-9021.",
            category="Bill / invoice help",
            status="Open",
            created_at=datetime.utcnow().isoformat()
        )
        sc2 = SupportCase(
            case_id="CAS-FAQ-88",
            user_id=user2_id,
            title="Request for Product Manual",
            description="Looking for the PDF user manual for dishwasher model LDT7819BD.",
            category="General FAQ",
            status="Resolved",
            created_at=datetime.utcnow().isoformat()
        )
        db.add_all([sc1, sc2])

        db.commit()
    finally:
        db.close()

@app.on_event("startup")
def startup_event():
    seed_database()

@app.get("/")
def root():
    return RedirectResponse(url="/docs")

app.include_router(api_router, prefix=settings.API_V1_STR)
