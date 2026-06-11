from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database.session import Base

class CallSession(Base):
    __tablename__ = "call_sessions"

    call_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=True)
    transcript = Column(String, nullable=True)       # Stringified JSON array of dialogue turns
    summary = Column(String, nullable=True)          # Text summary generated at the end of the call
    appointment_id = Column(String, ForeignKey("appointments.appointment_id", ondelete="SET NULL"), nullable=True)
    status = Column(String, nullable=False, default="Active")  # Active, Completed, Ended

    user = relationship("User", back_populates="call_sessions")
    appointment = relationship("Appointment")
