from pydantic import BaseModel, Field, EmailStr
from datetime import date, datetime
from typing import Optional, List

class UserSchema(BaseModel):
    user_id: str
    username: str
    password_hash: str
    full_name: str
    email: str
    phone: str
    address: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None

class ProductSchema(BaseModel):
    product_id: str
    user_id: str
    category: str
    model_number: str
    serial_number: str
    purchase_date: date
    warranty_status: str
    installation_date: Optional[date] = None

class OrderSchema(BaseModel):
    order_id: str
    user_id: str
    product_name: str
    status: str
    registered_phone: str
    registered_email: str
    created_at: datetime

class AppointmentSchema(BaseModel):
    appointment_id: str
    user_id: str
    customer_name: str
    product_category: str
    product_model: str
    serial_number: str
    purchase_date: date
    warranty_status: str
    issue_description: str
    address: str
    city: str
    pincode: str
    preferred_date: date
    preferred_time_slot: str
    status: str = "Scheduled"
    technician_name: Optional[str] = "Certified Tech"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SupportCaseSchema(BaseModel):
    case_id: str
    user_id: str
    title: str
    description: str
    status: str = "Open"
    category: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
