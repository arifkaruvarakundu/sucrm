# app/routers/upload.py
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app import models
from app.database import get_db
import pandas as pd

router = APIRouter()

@router.post("/upload-file/")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Read raw file bytes (for safe storage)
    raw_bytes = await file.read()

    # Reset pointer for pandas
    from io import BytesIO
    buffer = BytesIO(raw_bytes)

    # Parse with pandas
    if file.filename.endswith(".csv"):
        df = pd.read_csv(buffer)
    else:
        df = pd.read_excel(buffer)

    # Clean / normalize
    df = df.dropna(how="all")  
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Create UploadedFile entry
    uploaded = models.UploadedFile(
        filename=file.filename,
        file_type=file.content_type,
        total_rows=len(df),
        total_columns=len(df.columns),
        file_data=raw_bytes,
    )
    db.add(uploaded)
    db.commit()
    db.refresh(uploaded)

    # Save schema (column metadata)
    for col in df.columns:
        db.add(models.FileColumn(file_id=uploaded.id, name=col, dtype=str(df[col].dtype)))

    # Save rows as JSON
    for _, row in df.iterrows():
        db.add(models.FileRow(file_id=uploaded.id, data=row.to_dict()))

    db.commit()
    db.refresh(uploaded)

    return {
        "id": uploaded.id,
        "filename": uploaded.filename,
        "rows": uploaded.total_rows,
        "columns": uploaded.total_columns
    }
