from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.order.operation_helper import get_orders_in_range, get_orders_aggregated
import math

router = APIRouter(prefix = "/order-analysis", tags=["order-analysis"])

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

@router.get("/orders-in-range")
def orders_in_range(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    db: Session = Depends(get_db)
):

    """Return all orders between the given date range with details."""

    response = get_orders_in_range(db, start_date, end_date)
    safe_results = sanitize_for_json(response)

    return safe_results

@router.get("/orders-in-graph")
def orders_in_range(
    start_date: str,
    end_date: str,
    granularity: str = "daily",
    db: Session = Depends(get_db)
):
    return get_orders_aggregated(db, start_date, end_date, granularity)
