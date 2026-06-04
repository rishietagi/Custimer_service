from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database.session import Base

class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    product_name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    registered_phone = Column(String, nullable=False)
    registered_email = Column(String, nullable=False)
    created_at = Column(String, nullable=False)

    owner = relationship("User", back_populates="orders")
