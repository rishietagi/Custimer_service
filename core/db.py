import sqlite3
import os
from datetime import datetime

DB_FILE = "customer_service.db"

def get_connection():
    """Returns a SQLite connection. Creates the DB file if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema if tables do not exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        address TEXT,
        city TEXT,
        pincode TEXT
    );
    """)

    # Products Table (customer appliances)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        category TEXT NOT NULL,
        model_number TEXT NOT NULL,
        serial_number TEXT NOT NULL,
        purchase_date TEXT NOT NULL,
        warranty_status TEXT NOT NULL,
        installation_date TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # Orders Table (orders for new appliances/services)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        product_name TEXT NOT NULL,
        status TEXT NOT NULL,
        registered_phone TEXT NOT NULL,
        registered_email TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # Appointments Table (scheduled repairs/maintenance)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        appointment_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        customer_name TEXT NOT NULL,
        product_category TEXT NOT NULL,
        product_model TEXT NOT NULL,
        serial_number TEXT NOT NULL,
        purchase_date TEXT NOT NULL,
        warranty_status TEXT NOT NULL,
        issue_description TEXT NOT NULL,
        address TEXT NOT NULL,
        city TEXT NOT NULL,
        pincode TEXT NOT NULL,
        preferred_date TEXT NOT NULL,
        preferred_time_slot TEXT NOT NULL,
        status TEXT NOT NULL,
        technician_name TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # Support Cases Table (generic customer issues/tickets)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS support_cases (
        case_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        status TEXT NOT NULL,
        category TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()

# --- USER OPERATIONS ---

def create_user(user_id: str, username: str, password_hash: str, full_name: str, email: str, phone: str, address: str = None, city: str = None, pincode: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO users (user_id, username, password_hash, full_name, email, phone, address, city, pincode)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username.lower(), password_hash, full_name, email, phone, address, city, pincode))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_by_username(username: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username.lower(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(user_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# --- PRODUCT OPERATIONS ---

def add_product(product_id: str, user_id: str, category: str, model_number: str, serial_number: str, purchase_date: str, warranty_status: str, installation_date: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO products (product_id, user_id, category, model_number, serial_number, purchase_date, warranty_status, installation_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (product_id, user_id, category, model_number, serial_number, purchase_date, warranty_status, installation_date))
    conn.commit()
    conn.close()

def get_user_products(user_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# --- ORDER OPERATIONS ---

def add_order(order_id: str, user_id: str, product_name: str, status: str, registered_phone: str, registered_email: str, created_at: str = None):
    if not created_at:
        created_at = datetime.utcnow().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO orders (order_id, user_id, product_name, status, registered_phone, registered_email, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (order_id, user_id, product_name, status, registered_phone, registered_email, created_at))
    conn.commit()
    conn.close()

def get_user_orders(user_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def lookup_order(order_id: str, contact_info: str):
    """
    Looks up an order by order_id AND checks if registered_phone or registered_email matches contact_info.
    This provides basic validation.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM orders 
    WHERE UPPER(order_id) = UPPER(?) AND (UPPER(registered_phone) = UPPER(?) OR UPPER(registered_email) = UPPER(?))
    """, (order_id.strip(), contact_info.strip(), contact_info.strip()))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# --- APPOINTMENT OPERATIONS ---

def create_appointment(appointment_id: str, user_id: str, customer_name: str, product_category: str, product_model: str, serial_number: str, purchase_date: str, warranty_status: str, issue_description: str, address: str, city: str, pincode: str, preferred_date: str, preferred_time_slot: str, status: str = "Scheduled", technician_name: str = "Certified Tech"):
    created_at = datetime.utcnow().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO appointments (appointment_id, user_id, customer_name, product_category, product_model, serial_number, purchase_date, warranty_status, issue_description, address, city, pincode, preferred_date, preferred_time_slot, status, technician_name, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (appointment_id, user_id, customer_name, product_category, product_model, serial_number, purchase_date, warranty_status, issue_description, address, city, pincode, preferred_date, preferred_time_slot, status, technician_name, created_at))
    conn.commit()
    conn.close()

def get_user_appointments(user_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appointments WHERE user_id = ? ORDER BY preferred_date ASC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def reschedule_appointment(appointment_id: str, new_date: str, new_slot: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE appointments 
    SET preferred_date = ?, preferred_time_slot = ?, status = 'Rescheduled'
    WHERE appointment_id = ?
    """, (new_date, new_slot, appointment_id))
    conn.commit()
    conn.close()

def cancel_appointment(appointment_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE appointments 
    SET status = 'Cancelled'
    WHERE appointment_id = ?
    """, (appointment_id,))
    conn.commit()
    conn.close()

# --- SUPPORT CASE OPERATIONS ---

def create_support_case(case_id: str, user_id: str, title: str, description: str, category: str, status: str = "Open"):
    created_at = datetime.utcnow().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO support_cases (case_id, user_id, title, description, status, category, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (case_id, user_id, title, description, status, category, created_at))
    conn.commit()
    conn.close()

def get_user_support_cases(user_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM support_cases WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
