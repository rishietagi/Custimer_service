from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database.session import Base

class Product(Base):
    __tablename__ = "products"

    product_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    category = Column(String, nullable=False)
    model_number = Column(String, nullable=False)
    serial_number = Column(String, nullable=False)
    purchase_date = Column(String, nullable=False)
    warranty_status = Column(String, nullable=False)
    installation_date = Column(String, nullable=True)

    owner = relationship("User", back_populates="products")
