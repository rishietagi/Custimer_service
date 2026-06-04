import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from backend.app.database.session import get_db
from backend.app.models.support_case import SupportCase
from backend.app.schemas.support_case import SupportCaseResponse, SupportCaseCreate

router = APIRouter(prefix="/support-cases", tags=["Support Cases"])

@router.get("/user/{user_id}", response_model=List[SupportCaseResponse])
def get_user_tickets(user_id: str, db: Session = Depends(get_db)):
    return db.query(SupportCase).filter(SupportCase.user_id == user_id).order_by(SupportCase.created_at.desc()).all()

@router.post("", response_model=SupportCaseResponse)
def create_ticket(
    payload: SupportCaseCreate, 
    user_id: str = Query(..., description="ID of the user creating the ticket"),
    db: Session = Depends(get_db)
):
    case_id = "CAS-" + str(uuid.uuid4())[:8].upper()
    new_case = SupportCase(
        case_id=case_id,
        user_id=user_id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        status=payload.status or "Open",
        created_at=datetime.utcnow().isoformat()
    )
    db.add(new_case)
    db.commit()
    db.refresh(new_case)
    return new_case
