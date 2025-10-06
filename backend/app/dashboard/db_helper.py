from sqlalchemy.orm import Session
from app import models
from app.models import FileRow, UploadedFile, ColumnMapping
from sqlalchemy import func, cast, String, and_, Date, and_, or_, desc, literal_column, select

ANALYSIS_FIELDS = {
    "order": ["orderId","orderDate","quantity","totalAmount","orderStatus","customerName","customerPhone"],
    "customer": ["customerId","customerName","email","phone","city"],
    "product": ["productId","productName","category","price","quantity"],
}

def get_dashboard_data_from_db(db: Session, limit: int = 5, user_id: int | None = None, guest_id: str | None = None):
    query = db.query(models.FileRow).join(models.UploadedFile, FileRow.file_id == UploadedFile.id)

    if user_id:
        query = query.filter(UploadedFile.user_id == user_id)
    elif guest_id:
        query = query.filter(UploadedFile.guest_id == guest_id)

    rows = query.order_by(cast(models.FileRow.data.op('->>')('date'), Date).desc()).limit(limit).all()

    return [
        {
            "row_id": r.id,
            "file_id": r.file_id,
            "file_name": r.file.filename if r.file else None,
            "data": r.data,
        }
        for r in rows
    ]

def get_total_orders_count_data_from_db(db: Session, identity: dict, file_id: int | None = None) -> dict:
    """
    Returns total orders count for a given file or the latest file of the user/guest.
    """
    user = identity.get("user")
    guest_id = identity.get("guest_id")
    if not user and not guest_id:
        return {"count": 0, "file_id": None}

    user_id = getattr(user, "id", None) if user else None

    # Step 1: Determine target file
    if file_id:
        target_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if not target_file:
            return {"count": 0, "file_id": None}
        # Check ownership
        if user_id and target_file.user_id != user_id:
            return {"count": 0, "file_id": target_file.id}
        if guest_id and target_file.guest_id != guest_id:
            return {"count": 0, "file_id": target_file.id}
    else:
        target_file = (
            db.query(UploadedFile)
            .filter(
                (UploadedFile.user_id == user_id if user_id else False) |
                (UploadedFile.guest_id == guest_id if guest_id else False)
            )
            .order_by(UploadedFile.uploaded_at.desc())
            .first()
        )
        if not target_file:
            return {"count": 0, "file_id": None}

    # Step 2: Get order mapping
    mapping_obj = (
        db.query(ColumnMapping)
        .filter(
            ColumnMapping.file_id == target_file.id,
            ColumnMapping.analysis_type == "order"
        )
        .order_by(ColumnMapping.updated_at.desc())
        .first()
    )
    if not mapping_obj or "orderId" not in mapping_obj.mapping:
        return {"count": 0, "file_id": target_file.id}

    order_col = mapping_obj.mapping["orderId"]

    # Step 3: Count rows with non-empty order column
    count = (
        db.query(func.count(FileRow.id))
        .join(UploadedFile, FileRow.file_id == UploadedFile.id)
        .filter(FileRow.file_id == target_file.id)
        .filter(FileRow.data[order_col].astext.isnot(None))
        .filter(FileRow.data[order_col].astext != "")
    ).scalar() or 0

    return {"file_id": target_file.id, "count": count}