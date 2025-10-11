from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator
from app.models import User
from app.database import get_db
from app.utils.auth import hash_password, verify_password, create_access_token
from app import models
from typing import Optional

router = APIRouter()

# 🧩 Pydantic schema for registration
class UserRegister(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    confirm_password: str
    user_type: str  # "user" or "admin"

    @validator("confirm_password")
    def passwords_match(cls, v, values):
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v

    @validator("user_type")
    def valid_user_type(cls, v):
        allowed = ["user", "admin"]
        if v.lower() not in allowed:
            raise ValueError(f"user_type must be one of {allowed}")
        return v.lower()

# For login (simpler)
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    user_type: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    email: EmailStr
    user_type: Optional[str] = None

@router.post("/register", response_model=TokenResponse)
def register(user: UserRegister, request: Request, response: Response, db: Session = Depends(get_db)):
    # 🧠 Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 🔐 Hash password
    hashed_pw = hash_password(user.password)

    # 🧍 Create new user (can be 'admin' or 'user')
    new_user = User(
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        hashed_password=hashed_pw,
        user_type=user.user_type  # store the user_type
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 🧩 If guest files exist, transfer ownership to new user
    guest_id = request.cookies.get("guest_id")
    if guest_id:
        db.query(models.UploadedFile).filter(
            models.UploadedFile.guest_id == guest_id
        ).update(
            {
                models.UploadedFile.user_id: new_user.id,
                models.UploadedFile.guest_id: None,
            },
            synchronize_session=False,
        )

        if hasattr(models, "Guest"):
            db.query(models.Guest).filter(models.Guest.id == guest_id).delete()

        db.commit()
        response.delete_cookie("guest_id")

    # 🔑 Generate access token
    token = create_access_token({"sub": new_user.email, "user_type": new_user.user_type})

    return {
        "access_token": token,
        "token_type": "bearer",
        "email": new_user.email,
        "user_type": new_user.user_type,
    }

@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": db_user.email})
    return { "access_token": token, "token_type": "bearer","email": db_user.email, "user_type":db_user.user_type }
