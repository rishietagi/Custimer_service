from fastapi import APIRouter

from backend.app.routers.auth import router as auth_router
from backend.app.routers.users import router as users_router
from backend.app.routers.orders import router as orders_router
from backend.app.routers.appointments import router as appointments_router
from backend.app.routers.support_cases import router as support_cases_router
from backend.app.routers.chat import router as chat_router
from backend.app.routers.call_center import router as call_center_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(orders_router)
api_router.include_router(appointments_router)
api_router.include_router(support_cases_router)
api_router.include_router(chat_router)
api_router.include_router(call_center_router)

