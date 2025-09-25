from sqlalchemy.orm import Session
from app import models
from sqlalchemy import Date, cast
from app.models import FileRow
from sqlalchemy import func

def get_dashboard_data_from_db(db: Session, limit: int = 5):
  rows = (
    db.query(models.FileRow)
      .order_by(cast(models.FileRow.data.op('->>')('date'), Date).desc())
      .limit(limit)
      .all()
    )
  return [
    {
      "row_id": r.id,
      "file_id": r.file_id,
      "file_name": r.file.filename if r.file else None,
      "data": r.data,
    }
    for r in rows
  ]

def get_total_orders_count_data_from_db(db: Session):
  count = db.query(func.count(FileRow.id)).scalar()
  return {"count": count}