# # app/deps.py
# from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
# from sqlalchemy.orm import Session
# from jose import JWTError
# from app.utils.auth import decode_token
# from app.schemas import TokenData
# from app.database import get_db
# from app.models import User  # your SQLAlchemy User model

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")  # token endpoint

# def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"}
#     )
#     try:
#         token_data: TokenData = decode_token(token)
#         if not token_data or not token_data.email:
#             raise credentials_exception
#     except JWTError:
#         raise credentials_exception

#     user = db.query(User).filter(User.email == token_data.email).first()
#     if user is None:
#         raise credentials_exception
#     return user

# app/deps.py
from fastapi import Request, Response, Depends
from app.database import get_db
from app import models
from sqlalchemy.orm import Session
import uuid
from app.utils.auth import decode_token  # your JWT decode helper

def get_identity(request: Request, response: Response, db: Session = Depends(get_db)):
    """
    Return dict: { "user": User | None, "guest_id": str | None }
    If Authorization Bearer token present and valid => user returned.
    Otherwise ensure a guest_id cookie exists (create if missing) and return it.
    This dependency *can* set a cookie on the response.
    """
    # 1) try JWT
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            token_data = decode_token(token)  # returns TokenData(email=...)
            print("Decoded token email:", token_data.email) 
            user = db.query(models.User).filter(models.User.email == token_data.email).first()
            print("DB user found:", user)
            if user:
                return {"user": user, "guest_id": None}
        except Exception as e:
            print("Error decoding token:", e)

    # 2) handle guest cookie
    guest_id = request.cookies.get("guest_id")
    if guest_id:
        # Optionally validate guest exists; if not, create a new one
        guest = db.query(models.Guest).filter(models.Guest.id == guest_id).first()
        if guest:
            return {"user": None, "guest_id": guest_id}

    # Create new guest
    new_guest_id = str(uuid.uuid4())
    guest = models.Guest(id=new_guest_id)
    db.add(guest)
    db.commit()
    db.refresh(guest)

    # set cookie - httpOnly, secure in prod
    response.set_cookie(
        key="guest_id",
        value=new_guest_id,
        httponly=True,
        # secure=True,
        samesite="lax",
        max_age=30 * 24 * 3600  # 30 days (adjust)
    )
    return {"user": None, "guest_id": new_guest_id}
