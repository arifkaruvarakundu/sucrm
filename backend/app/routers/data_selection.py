from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import desc, or_
from app.database import get_db
from app.utils.deps import get_identity
from app.models import FileColumn, ColumnMapping, UploadedFile

router = APIRouter()

ANALYSIS_FIELDS = {
    "order": ["orderId", "orderDate", "quantity", "totalAmount", "orderStatus", "customerName", "customerPhone"],
    "customer": ["customerId", "customerName", "email", "phone", "city"],
    "product": ["productId", "productName", "category", "price", "quantity"],
}

class MappingPayload(BaseModel):
    file_id: Optional[int] = None
    selected_analyses: List[str]
    mapping: Dict[str, str]

@router.post("/column-mapping")
def save_mapping(payload: MappingPayload, db: Session = Depends(get_db), identity: dict = Depends(get_identity)):
    # Determine user or guest
    if identity["user"]:
        user_id = identity["user"].id
        guest_id = None
    else:
        user_id = None
        guest_id = identity["guest_id"]

    # Find file_id if not provided
    file_id = payload.file_id
    if not file_id:
        latest_file = (
            db.query(UploadedFile)
            .filter(or_(UploadedFile.user_id == user_id, UploadedFile.guest_id == guest_id))
            .order_by(desc(UploadedFile.uploaded_at))
            .first()
        )
        if not latest_file:
            raise HTTPException(400, "No uploaded files found for this user/guest to attach mapping.")
        file_id = latest_file.id

    # ✅ STEP 1: Store column names in FileColumn if not already saved
    existing_cols = {fc.name.lower() for fc in db.query(FileColumn).filter(FileColumn.file_id == file_id).all()}

    new_columns = []
    for user_col_name in payload.mapping.values():
        if user_col_name.lower() not in existing_cols:
            new_columns.append(FileColumn(file_id=file_id, name=user_col_name, dtype="string"))

    if new_columns:
        db.add_all(new_columns)
        db.commit()

    # ✅ STEP 2: Create column mappings (as before)
    for analysis in payload.selected_analyses:
        if analysis not in ANALYSIS_FIELDS:
            raise HTTPException(400, f"Unknown analysis type: {analysis}")

        allowed_keys = set(ANALYSIS_FIELDS[analysis])
        mapping_for_analysis = {k: v for k, v in payload.mapping.items() if k in allowed_keys}

        mapping_for_analysis = {k: v for k, v in mapping_for_analysis.items() if v and str(v).strip() != ""}
        if not mapping_for_analysis:
            continue

        existing = (
            db.query(ColumnMapping)
            .filter_by(file_id=file_id, user_id=user_id, analysis_type=analysis)
            .first()
        )

        if existing:
            existing.mapping = mapping_for_analysis
            existing.updated_at = datetime.utcnow()
        else:
            cm = ColumnMapping(
                file_id=file_id,
                user_id=user_id,
                guest_id=guest_id,
                analysis_type=analysis,
                mapping=mapping_for_analysis,
                is_default=False
            )
            db.add(cm)

    db.commit()
    return {"ok": True, "file_id": file_id}
