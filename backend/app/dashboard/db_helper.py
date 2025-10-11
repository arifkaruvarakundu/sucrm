from sqlalchemy.orm import Session
from app import models
from app.models import FileRow, UploadedFile, ColumnMapping
from sqlalchemy import func, cast, String, and_, Date, and_, or_, desc, literal_column, select

ANALYSIS_FIELDS = {
    "order": ["orderId", "orderDate", "quantity", "totalAmount", "orderStatus", "customerName", "customerPhone"],
    "customer": ["customerId", "customerName", "email", "phone", "city"],
    "product": ["productId", "productName", "category", "price", "quantity"]
}

def get_dashboard_data_from_db(db: Session, identity: dict, file_id: int | None, limit: int):
    
    user = identity.get("user")
    guest_id = identity.get("guest_id")
    if not user and not guest_id:
        return {"file_id": None, "file_name": None, "rows": []}

    user_id = getattr(user, "id", None) if user else None

    # Step 1: Determine target file
    if file_id:
        target_file = db.query(models.UploadedFile).filter(models.UploadedFile.id == file_id).first()
        if not target_file:
            return {"file_id": None, "file_name": None, "rows": []}
        if user_id and target_file.user_id != user_id:
            return {"file_id": None, "file_name": None, "rows": []}
        if guest_id and target_file.guest_id != guest_id:
            return {"file_id": None, "file_name": None, "rows": []}
    else:
        filters = []
        if user_id:
            filters.append(models.UploadedFile.user_id == user_id)
        if guest_id:
            filters.append(models.UploadedFile.guest_id == guest_id)
        if not filters:
            return {"file_id": None, "file_name": None, "rows": []}

        target_file = (
            db.query(models.UploadedFile)
            .filter(or_(*filters))
            .order_by(models.UploadedFile.uploaded_at.desc())
            .first()
        )
        if not target_file:
            return {"file_id": None, "file_name": None, "rows": []}

    # Step 2: Get column mapping for "order" analysis
    mapping_obj = (
        db.query(models.ColumnMapping)
        .filter(
            models.ColumnMapping.file_id == target_file.id,
            models.ColumnMapping.analysis_type == "order"
        )
        .order_by(models.ColumnMapping.updated_at.desc())
        .first()
    )

    if not mapping_obj or "orderId" not in mapping_obj.mapping:
        return {"file_id": target_file.id, "file_name": target_file.filename, "rows": []}

    order_col = mapping_obj.mapping["orderId"]
    date_col = mapping_obj.mapping.get("OrderDate")  # optional fallback

    # Step 3: Query valid orders only
    query = db.query(models.FileRow).filter(
        models.FileRow.file_id == target_file.id,
        models.FileRow.data[order_col].astext.isnot(None),
        models.FileRow.data[order_col].astext != ""
    )

    # Filter by user/guest ownership
    if user_id:
        query = query.join(models.UploadedFile).filter(models.UploadedFile.user_id == user_id)
    elif guest_id:
        query = query.join(models.UploadedFile).filter(models.UploadedFile.guest_id == guest_id)

    # Step 4: Order by date if mapped, otherwise fallback to ID
    if date_col:
        query = query.order_by(cast(models.FileRow.data.op("->>")(date_col), Date).desc())
    else:
        query = query.order_by(models.FileRow.id.desc())

    # Limit rows
    rows = query.limit(limit).all()

    # Step 5: Format result
    result = [
        {
            "row_id": r.id,
            "file_id": r.file_id,
            "file_name": target_file.filename,
            "data": r.data,
        }
        for r in rows
    ]

    return {
        "file_id": target_file.id,
        "file_name": target_file.filename,
        "rows": result,
    }

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