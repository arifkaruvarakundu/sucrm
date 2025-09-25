from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.customer.operation_helper import get_customers_table, aggregate_customers_from_orders

router = APIRouter(prefix="/customer-analysis", tags=["customer-analysis"])

@router.get("/customers-table")
def customers_table(db: Session = Depends(get_db)):
    response = get_customers_table(db)
    return response


@router.get("/full-customer-classification")
def full_customer_classification(db: Session = Depends(get_db)):
    """Return per-customer aggregates: name, phone, order_count, total_spending, last_order_date."""
    results = aggregate_customers_from_orders(db)
    return results
