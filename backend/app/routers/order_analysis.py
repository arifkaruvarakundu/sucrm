from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.order.operation_helper import get_orders_in_range, get_orders_aggregated
import math
from app.utils.deps import get_identity
from typing import Optional

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
    db: Session = Depends(get_db),
    identity: dict = Depends(get_identity),
    file_id: Optional[int] = Query(None, description="Optional file ID to filter by")
):
    """Return detailed orders between given dates."""
    data = get_orders_in_range(db=db, start_date=start_date, end_date=end_date, identity=identity, file_id=file_id)
    return sanitize_for_json({
        "file_id": file_id,
        "columns": ["order_id", "customer_name", "date", "amount"],
        "rows": data
    })

@router.get("/orders-in-graph")
def orders_in_range(
    start_date: str,
    end_date: str,
    granularity: str = "daily",
    db: Session = Depends(get_db),
    identity: dict = Depends(get_identity),
    file_id: int | None = Query(None, description = "Optional file ID to filter by")
):
    print("identity:", identity)
    return get_orders_aggregated(db=db, start_date=start_date, end_date=end_date, granularity=granularity, identity= identity, file_id=file_id)
