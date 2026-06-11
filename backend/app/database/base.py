# Import all models here so that Base.metadata can detect them
from backend.app.database.session import Base
from backend.app.models.user import User
from backend.app.models.product import Product
from backend.app.models.order import Order
from backend.app.models.appointment import Appointment
from backend.app.models.support_case import SupportCase
from backend.app.models.chat_session import ChatSession
from backend.app.models.call_session import CallSession

