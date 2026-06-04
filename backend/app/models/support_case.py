from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database.session import Base

class SupportCase(Base):
    __tablename__ = "support_cases"

    case_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    status = Column(String, nullable=False, default="Open")
    category = Column(String, nullable=False)
    created_at = Column(String, nullable=False)

    owner = relationship("User", back_populates="support_cases")
