import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.models.product import Product
from backend.app.models.appointment import Appointment
from backend.app.models.order import Order
from backend.app.models.support_case import SupportCase
from backend.app.schemas.user import UserResponse
from backend.app.schemas.product import ProductCreate, ProductResponse
from backend.app.schemas.appointment import AppointmentResponse
from backend.app.schemas.order import OrderResponse
from backend.app.schemas.support_case import SupportCaseResponse

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/{user_id}/profile", response_model=UserResponse)
def get_profile(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user

@router.get("/{user_id}/dashboard")
def get_dashboard_summary(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    products = db.query(Product).filter(Product.user_id == user_id).all()
    appointments = db.query(Appointment).filter(Appointment.user_id == user_id).order_by(Appointment.preferred_date.asc()).all()
    orders = db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()
    support_cases = db.query(SupportCase).filter(SupportCase.user_id == user_id).order_by(SupportCase.created_at.desc()).all()
    
    return {
        "user": user,
        "products": products,
        "appointments": appointments,
        "orders": orders,
        "support_cases": support_cases
    }

@router.get("/{user_id}/products", response_model=List[ProductResponse])
def get_user_products(user_id: str, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.user_id == user_id).all()
    return products

@router.post("/{user_id}/products", response_model=ProductResponse)
def register_product(user_id: str, payload: ProductCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    product_id = "prod_" + str(uuid.uuid4())[:8]
    new_product = Product(
        product_id=product_id,
        user_id=user_id,
        category=payload.category,
        model_number=payload.model_number,
        serial_number=payload.serial_number.upper(),
        purchase_date=payload.purchase_date,
        warranty_status=payload.warranty_status,
        installation_date=payload.installation_date
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product
