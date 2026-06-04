from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database.session import Base

class Appointment(Base):
    __tablename__ = "appointments"

    appointment_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    customer_name = Column(String, nullable=False)
    product_category = Column(String, nullable=False)
    product_model = Column(String, nullable=False)
    serial_number = Column(String, nullable=False)
    purchase_date = Column(String, nullable=False)
    warranty_status = Column(String, nullable=False)
    issue_description = Column(String, nullable=False)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    pincode = Column(String, nullable=False)
    preferred_date = Column(String, nullable=False)
    preferred_time_slot = Column(String, nullable=False)
    status = Column(String, nullable=False, default="Scheduled")
    technician_name = Column(String, nullable=True, default="Certified Tech")
    created_at = Column(String, nullable=False)

    owner = relationship("User", back_populates="appointments")
