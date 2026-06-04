import hashlib
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.schemas.user import UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@router.post("/login", response_model=UserResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    username_lower = payload.username.strip().lower()
    user = db.query(User).filter(User.username == username_lower).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )
    
    hashed_payload_pass = hash_password(payload.password)
    if user.password_hash != hashed_payload_pass:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )
    
    return user

@router.post("/register", response_model=UserResponse)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    username_lower = payload.username.strip().lower()
    existing_user = db.query(User).filter(User.username == username_lower).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists. Please choose another."
        )
        
    user_id = "usr_" + str(uuid.uuid4())[:8]
    hashed_pass = hash_password(payload.password)
    
    new_user = User(
        user_id=user_id,
        username=username_lower,
        password_hash=hashed_pass,
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        address=payload.address,
        city=payload.city,
        pincode=payload.pincode
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
