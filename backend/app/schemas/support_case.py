from pydantic import BaseModel
from typing import Optional

class SupportCaseBase(BaseModel):
    title: str
    description: str
    category: str
    status: Optional[str] = "Open"

class SupportCaseCreate(SupportCaseBase):
    pass

class SupportCaseResponse(SupportCaseBase):
    case_id: str
    user_id: str
    created_at: str

    class Config:
        from_attributes = True
