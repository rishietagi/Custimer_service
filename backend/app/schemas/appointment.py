from pydantic import BaseModel
from typing import Optional

class AppointmentBase(BaseModel):
    customer_name: str
    product_category: str
    product_model: str
    serial_number: str
    purchase_date: str
    warranty_status: str
    issue_description: str
    address: str
    city: str
    pincode: str
    preferred_date: str
    preferred_time_slot: str

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentReschedule(BaseModel):
    preferred_date: str
    preferred_time_slot: str

class AppointmentResponse(AppointmentBase):
    appointment_id: str
    user_id: str
    status: str
    technician_name: Optional[str]
    created_at: str

    class Config:
        from_attributes = True
