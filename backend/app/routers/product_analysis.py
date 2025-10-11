from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.deps import get_identity
from app.product.operation_helper import get_top_selling_products, get_top_selling_products_by_date, get_products_sales_table

router = APIRouter(prefix="/product-analysis", tags=["product-analysis"])

@router.get("/top-products")
def top_products(limit: int = 5, file_id: int | None = None, db: Session = Depends(get_db), identity=Depends(get_identity)):
    return get_top_selling_products(db=db, identity=identity, file_id=file_id, limit=limit)

@router.get("/top-products-by-date")
def top_products_by_date(
    start_date: str,
    end_date: str,
    limit: int = 5,
    file_id: int | None = None,
    db: Session = Depends(get_db),
    identity=Depends(get_identity)
):
    return get_top_selling_products_by_date(
        db=db, identity=identity, start_date=start_date, end_date=end_date, limit=limit, file_id=file_id
    )

@router.get("/products-sales-table")
def products_sales_table(
    start_date: str,
    end_date: str,
    file_id: int | None = None,
    db: Session = Depends(get_db),
    identity=Depends(get_identity),
):
    response = get_products_sales_table(db, identity, start_date, end_date, file_id)
    return response

