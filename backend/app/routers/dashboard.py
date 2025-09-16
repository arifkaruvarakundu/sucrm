from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dashboard.operation_helper import get_dashboard_data
from typing import List

router = APIRouter()

@router.get("/dashboard", response_model=List[dict])
def dashboard_data(db: Session = Depends(get_db)):

    response_data = get_dashboard_data(db=db)

    return response_data


