import hashlib
import uuid
from datetime import datetime, date, timedelta
from core.db import get_connection, init_db, create_user, add_product, add_order, create_appointment, create_support_case

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def seed_data():
    """Seeds the database with high-quality dummy data if it is empty."""
    init_db()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()

    if count > 0:
        # Database already has data, skip seeding
        return

    # 1. Create Users
    user1_id = "usr_" + str(uuid.uuid4())[:8]
    create_user(
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

    user2_id = "usr_" + str(uuid.uuid4())[:8]
    create_user(
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

    # 2. Add Products for Users
    add_product(
        product_id="prod_" + str(uuid.uuid4())[:8],
        user_id=user1_id,
        category="Refrigerator",
        model_number="LFXS26973S",
        serial_number="REF987654321",
        purchase_date=(date.today() - timedelta(days=500)).isoformat(),
        warranty_status="In Warranty",
        installation_date=(date.today() - timedelta(days=495)).isoformat()
    )

    add_product(
        product_id="prod_" + str(uuid.uuid4())[:8],
        user_id=user1_id,
        category="Washing Machine",
        model_number="WM4000HBA",
        serial_number="WASH11223344",
        purchase_date=(date.today() - timedelta(days=200)).isoformat(),
        warranty_status="In Warranty",
        installation_date=(date.today() - timedelta(days=198)).isoformat()
    )

    add_product(
        product_id="prod_" + str(uuid.uuid4())[:8],
        user_id=user2_id,
        category="Dishwasher",
        model_number="LDT7819BD",
        serial_number="DISH88776655",
        purchase_date=(date.today() - timedelta(days=800)).isoformat(),
        warranty_status="Out of Warranty",
        installation_date=(date.today() - timedelta(days=795)).isoformat()
    )

    # 3. Add Orders for Users
    # John's orders
    add_order(
        order_id="ORD-9021",
        user_id=user1_id,
        product_name="OLED C3 55-inch TV",
        status="Delivered",
        registered_phone="5550199283",
        registered_email="john.doe@support-example.com",
        created_at=(datetime.now() - timedelta(days=10)).isoformat()
    )

    add_order(
        order_id="ORD-4482",
        user_id=user1_id,
        product_name="NeoChef Countertop Microwave",
        status="Shipped",
        registered_phone="5550199283",
        registered_email="john.doe@support-example.com",
        created_at=(datetime.now() - timedelta(days=2)).isoformat()
    )

    # Jane's orders
    add_order(
        order_id="ORD-1153",
        user_id=user2_id,
        product_name="SmartCare Smart Wi-Fi Front Control Dryer",
        status="Delayed",
        registered_phone="5550188722",
        registered_email="jane.smith@support-example.com",
        created_at=(datetime.now() - timedelta(days=5)).isoformat()
    )

    add_order(
        order_id="ORD-5531",
        user_id=user2_id,
        product_name="QuadWash Pro Dishwasher",
        status="Installation Pending",
        registered_phone="5550188722",
        registered_email="jane.smith@support-example.com",
        created_at=(datetime.now() - timedelta(days=1)).isoformat()
    )

    # 4. Add Appointments
    create_appointment(
        appointment_id="APT-" + str(uuid.uuid4())[:8].upper(),
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
        preferred_time_slot="09:00 AM - 12:00 PM",
        status="Scheduled",
        technician_name="Sarah Miller (Ref Expert)"
    )

    create_appointment(
        appointment_id="APT-" + str(uuid.uuid4())[:8].upper(),
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
        preferred_time_slot="02:00 PM - 05:00 PM",
        status="Scheduled",
        technician_name="David Chen (Appliance Specialist)"
    )

    # 5. Add Support Cases
    create_support_case(
        case_id="CAS-" + str(uuid.uuid4())[:8].upper(),
        user_id=user1_id,
        title="Double Charged Invoice",
        description="I was charged twice on my credit card for the OLED TV purchase. Order ORD-9021.",
        category="Bill / invoice help",
        status="Open"
    )

    create_support_case(
        case_id="CAS-" + str(uuid.uuid4())[:8].upper(),
        user_id=user2_id,
        title="Request for Product Manual",
        description="Looking for the PDF user manual for dishwasher model LDT7819BD.",
        category="General FAQ",
        status="Resolved"
    )
