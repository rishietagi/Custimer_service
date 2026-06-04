from pydantic import BaseModel
from typing import Optional

class ProductBase(BaseModel):
    category: str
    model_number: str
    serial_number: str
    purchase_date: str
    warranty_status: str
    installation_date: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    product_id: str
    user_id: str

    class Config:
        from_attributes = True
