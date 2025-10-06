from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.customer.operation_helper import get_customers_table, aggregate_customers_from_orders
import math
from app.utils.deps import get_identity

router = APIRouter(prefix="/customer-analysis", tags=["customer-analysis"])

@router.get("/customers-table")
def customers_table(
    identity: dict = Depends(get_identity),
    db: Session = Depends(get_db)
):

    user = identity["user"]
    guest_id = identity["guest_id"]

    response = get_customers_table(
        db,
        user_id=user.id if user else None,
        guest_id=guest_id,
    )
    
    return response

def sanitize_for_json(obj):
    """Recursively replace NaN/inf floats with None so JSON is valid."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    return obj

@router.get("/full-customer-classification")
def full_customer_classification(db: Session = Depends(get_db)):
    """Return per-customer aggregates: name, phone, order_count, total_spending, last_order_date."""
    results = aggregate_customers_from_orders(db)
    safe_results = sanitize_for_json(results)
    return safe_results