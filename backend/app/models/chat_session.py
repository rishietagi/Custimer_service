from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database.session import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    current_state = Column(String, nullable=False, default="HOME_MENU")
    chat_data = Column(String, nullable=False, default="{}")       # JSON stringified dict
    state_history = Column(String, nullable=False, default="[]")   # JSON stringified list of states
    messages = Column(String, nullable=False, default="[]")        # JSON stringified list of messages
    updated_at = Column(String, nullable=False)

    user = relationship("User", back_populates="chat_sessions")
