from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.product.operation_helper import get_top_selling_products, get_top_selling_products_by_date, get_products_sales_table

router = APIRouter(prefix="/product-analysis", tags=["product-analysis"])

@router.get("/top-products")
def top_products(limit: int = 5, db: Session = Depends(get_db)):

    response = get_top_selling_products(db, limit)

    return response

@router.get("/top-products-by-date")
def top_products_by_date(
    start_date: str,
    end_date: str,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    response = get_top_selling_products_by_date(db, start_date, end_date, limit)
    return response

@router.get("/products-sales-table")
def products_sales_table(
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db)
):
    response = get_products_sales_table(db, start_date, end_date)

    return response

