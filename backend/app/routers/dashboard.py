from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dashboard.operation_helper import get_dashboard_data, get_top_customers, get_total_orders_count, get_total_sales, get_total_customers, get_total_products


router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/latest-rows")
def latest_rows(limit: int = 5, db: Session = Depends(get_db)):
    response = get_dashboard_data(db, limit)
    return response

@router.get("/top-customers")
def top_customers(limit: int = 5, db: Session = Depends(get_db)):
    response = get_top_customers(db, limit)
    return response

@router.get("/total-orders-count")
def total_orders_count(db: Session = Depends(get_db)):
    response = get_total_orders_count(db)
    return response

@router.get("/total-sales")
def total_sales(db: Session = Depends(get_db)):
    response = get_total_sales(db)
    return response

@router.get("/total-customers")
def total_customers(db: Session = Depends(get_db)):
    response = get_total_customers(db)
    return response

@router.get("/total-products")
def total_products(db: Session = Depends(get_db)):
    response = get_total_products(db)
    return response

