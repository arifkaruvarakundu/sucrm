from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dashboard.operation_helper import get_dashboard_data, get_top_customers, get_total_orders_count, get_total_sales, get_total_customers, get_total_products
from app.utils.deps import get_identity
from fastapi import Query, Request

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/latest-rows")
def latest_rows(db: Session = Depends(get_db), identity = Depends(get_identity), file_id: int | None = Query(None, description="Optional file ID to filter by"), limit: int = 5):

    response = get_dashboard_data(db=db, identity=identity, file_id=file_id, limit=limit)
    
    return response

@router.get("/top-customers")
def top_customers(request: Request, limit: int = 5, db: Session = Depends(get_db), identity: dict = Depends(get_identity), file_id: int | None = Query(None, description = "Optional file ID to filter by")):

    response = get_top_customers(db=db, identity=identity, limit=limit, file_id=file_id)

    return response

@router.get("/total-orders-count")
def total_orders_count(db: Session = Depends(get_db), identity: dict = Depends(get_identity), file_id: int | None = Query(None, description="Optional file ID to filter by")):

    response = get_total_orders_count(db, identity, file_id)

    return response

@router.get("/total-sales")
def total_sales(db: Session = Depends(get_db), identity: dict = Depends(get_identity), file_id: int | None = Query(None, description="Optional file ID to filter by")):

    response = get_total_sales(db, identity, file_id)

    return response

@router.get("/total-customers")
def total_customers(db: Session = Depends(get_db), identity: dict = Depends(get_identity), file_id: int | None = Query(None, description="Optional file ID")):

    """
    Returns total unique customers for a specific file or the latest file of the user/guest.
    """
    response = get_total_customers(db, identity, file_id)

    return response

@router.get("/total-products")
def total_products(db: Session = Depends(get_db), identity: dict = Depends(get_identity), file_id: int | None = Query(None, description="Optional file ID")):

    """
    Returns total products for a specific file or the latest file of the user/guest.
    """

    response = get_total_products(db, identity, file_id)

    return response



