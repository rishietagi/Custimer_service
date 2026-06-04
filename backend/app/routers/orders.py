import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List

from backend.app.database.session import get_db
from backend.app.models.order import Order
from backend.app.models.support_case import SupportCase
from backend.app.models.user import User
from backend.app.schemas.order import OrderResponse, OrderCreate
from backend.app.schemas.support_case import SupportCaseCreate, SupportCaseResponse

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.get("/lookup", response_model=OrderResponse)
def lookup_order(
    order_id: str = Query(..., description="ID of the order to track"),
    contact_info: str = Query(..., description="Registered email or phone number")
):
    # Lookup is performed inside DB Session directly
    # We will get database connection inside this function
    from backend.app.database.session import SessionLocal
    db = SessionLocal()
    try:
        order = db.query(Order).filter(
            Order.order_id.ilike(order_id.strip()),
            (Order.registered_phone.ilike(contact_info.strip()) | Order.registered_email.ilike(contact_info.strip()))
        ).first()
        if not order:
            raise HTTPException(
                status_code=404, 
                detail="No order found matching this Order ID and contact details. Please check and try again."
            )
        return order
    finally:
        db.close()

@router.get("/user/{user_id}", response_model=List[OrderResponse])
def get_user_orders(user_id: str, db: Session = Depends(get_db)):
    return db.query(Order).filter(Order.user_id == user_id).all()

@router.post("/{order_id}/callback")
def request_callback(order_id: str, user_id: str = Query(...), db: Session = Depends(get_db)):
    # Verify order exists
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    
    # Request callback has no formal DB table, but we return details
    return {
        "message": f"Callback requested successfully. A support executive will call you at {order.registered_phone} within 2 to 4 business hours.",
        "order_id": order_id,
        "registered_phone": order.registered_phone
    }

@router.post("/{order_id}/escalate", response_model=SupportCaseResponse)
def escalate_order(order_id: str, user_id: str = Query(...), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
        
    ticket_id = "CAS-ORD-" + str(uuid.uuid4())[:6].upper()
    ticket = SupportCase(
        case_id=ticket_id,
        user_id=user_id,
        title=f"Order Escalation: {order_id}",
        description=f"User escalated order status inquiry for order {order_id} ({order.product_name}). Current status: {order.status}.",
        category="Complaint escalation",
        status="Open",
        created_at=datetime.utcnow().isoformat()
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

@router.post("/{order_id}/complaint", response_model=SupportCaseResponse)
def submit_order_complaint(
    order_id: str, 
    payload: SupportCaseCreate, 
    user_id: str = Query(...), 
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
        
    ticket_id = "CAS-ORD-" + str(uuid.uuid4())[:6].upper()
    ticket = SupportCase(
        case_id=ticket_id,
        user_id=user_id,
        title=f"Order Complaint: {payload.title}",
        description=f"Order ID: {order_id}\nDescription: {payload.description}",
        category="Complaint escalation",
        status="Open",
        created_at=datetime.utcnow().isoformat()
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket
