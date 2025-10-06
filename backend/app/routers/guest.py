from fastapi import APIRouter, Response, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
import uuid

router = APIRouter()

@router.post("/guest-session")
def create_guest_session(response: Response, db: Session = Depends(get_db)):
    guest_id = str(uuid.uuid4())
    guest = models.Guest(id=guest_id)
    db.add(guest)
    db.commit()
    response.set_cookie("guest_id", guest_id, httponly=True, samesite="lax", max_age=30*24*3600)
    return {"guest_id": guest_id}