from pydantic import BaseModel
from typing import Optional

class OrderBase(BaseModel):
    product_name: str
    status: str
    registered_phone: str
    registered_email: str

class OrderCreate(OrderBase):
    order_id: str
    user_id: str

class OrderResponse(OrderBase):
    order_id: str
    user_id: str
    created_at: str

    class Config:
        from_attributes = True

class OrderLookupRequest(BaseModel):
    order_id: str
    contact_info: str
