from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.app.database.session import get_db
from backend.app.models.appointment import Appointment
from backend.app.schemas.appointment import AppointmentResponse, AppointmentReschedule
from backend.app.core.validators import validate_future_date

router = APIRouter(prefix="/appointments", tags=["Appointments"])

@router.get("/user/{user_id}", response_model=List[AppointmentResponse])
def get_user_appointments(user_id: str, db: Session = Depends(get_db)):
    return db.query(Appointment).filter(Appointment.user_id == user_id).order_by(Appointment.preferred_date.asc()).all()

@router.put("/{appointment_id}/reschedule", response_model=AppointmentResponse)
def reschedule(appointment_id: str, payload: AppointmentReschedule, db: Session = Depends(get_db)):
    apt = db.query(Appointment).filter(Appointment.appointment_id == appointment_id).first()
    if not apt:
        raise HTTPException(status_code=404, detail="Appointment not found.")
        
    if apt.status == "Cancelled":
        raise HTTPException(status_code=400, detail="Cannot reschedule a cancelled appointment.")
        
    ok_date, err_date = validate_future_date(payload.preferred_date)
    if not ok_date:
        raise HTTPException(status_code=400, detail=err_date)
        
    apt.preferred_date = payload.preferred_date
    apt.preferred_time_slot = payload.preferred_time_slot
    apt.status = "Rescheduled"
    
    db.commit()
    db.refresh(apt)
    return apt

@router.put("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel(appointment_id: str, db: Session = Depends(get_db)):
    apt = db.query(Appointment).filter(Appointment.appointment_id == appointment_id).first()
    if not apt:
        raise HTTPException(status_code=404, detail="Appointment not found.")
        
    apt.status = "Cancelled"
    db.commit()
    db.refresh(apt)
    return apt
