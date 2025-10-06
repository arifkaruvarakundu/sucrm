from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator
from app.models import User
from app.database import get_db
from app.utils.auth import hash_password, verify_password, create_access_token
from app import models

router = APIRouter()

# 🧩 Pydantic schema for registration
class UserRegister(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    confirm_password: str

    @validator("confirm_password")
    def passwords_match(cls, v, values):
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v

# For login (simpler)
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    email: EmailStr

@router.post("/register", response_model=TokenResponse)
def register(user: UserRegister, request: Request, response: Response, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(user.password)
    new_user = User(
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        hashed_password=hashed_pw
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 🔑 Migrate guest-owned files if guest_id cookie exists
    guest_id = request.cookies.get("guest_id")
    if guest_id:
        # Update all files belonging to guest → assign to new user
        db.query(models.UploadedFile).filter(
            models.UploadedFile.guest_id == guest_id
        ).update(
            {
                models.UploadedFile.user_id: new_user.id,
                models.UploadedFile.guest_id: None
            },
            synchronize_session=False
        )

        # Optionally: if you maintain a Guest table, remove the guest row
        if hasattr(models, "Guest"):
            db.query(models.Guest).filter(models.Guest.id == guest_id).delete()

        db.commit()

        # Clear cookie on client so they don't keep using guest_id
        response.delete_cookie("guest_id")

    token = create_access_token({"sub": new_user.email})
    response_data = {
    "access_token": token,
    "token_type": "bearer",
    "email": new_user.email
    }

    return response_data

@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": db_user.email})
    return { "access_token": token, "token_type": "bearer","email": db_user.email }
