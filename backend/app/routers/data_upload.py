# app/routers/upload.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Response
from sqlalchemy.orm import Session
from app import models
from app.database import get_db
from app.utils.deps import get_identity 
import pandas as pd
from io import BytesIO
import cloudinary
import cloudinary.uploader
import time
import re
import traceback
import logging
import json
import math
from typing import Any

logger = logging.getLogger(__name__)

router = APIRouter()

# storing the data in both the cloudinary and database

def clean_json(obj):
    """Recursively replace NaN/Infinity/-Infinity with None for JSON compliance."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: clean_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_json(v) for v in obj]
    return obj

@router.post("/upload-file/")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db),  response: Response = None, identity = Depends(get_identity), ):
    try:
        # Read file content
        file_content = await file.read()

         # 🔒 Ownership from identity
        owner_user = identity["user"]
        owner_guest = identity["guest_id"]

        # Sanitize filename for Cloudinary
        public_id_safe = re.sub(r'[^A-Za-z0-9_-]', '_', file.filename)
        public_id = f"{public_id_safe}_{int(time.time())}"

        # Upload to Cloudinary as raw
        file_buffer = BytesIO(file_content)
        result = cloudinary.uploader.upload(
            file_buffer,
            resource_type="raw",
            folder="uploads",
            public_id=public_id
        )

        # Parse file with pandas
        buffer = BytesIO(file_content)
        try:
            if file.filename.endswith(".csv"):
                df = pd.read_csv(buffer)
            else:
                df = pd.read_excel(buffer, engine="openpyxl")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"File parsing failed: {str(e)}")

        # Normalize dataframe
        df = df.dropna(how="all")
        df.columns = [c.strip() for c in df.columns]
        # Convert datetime-like columns to ISO strings to make JSON-serializable
        try:
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = df[col].dt.strftime('%Y-%m-%dT%H:%M:%S')
        except Exception:
            pass
        # Ensure JSON-safe values
        df = df.where(pd.notnull(df), None)

        # Store UploadedFile metadata
        uploaded = models.UploadedFile(
            filename=file.filename,
            file_type=file.content_type,
            total_rows=len(df),
            total_columns=len(df.columns),
            file_data=file_content,
            cloudinary_url=result["secure_url"],
            cloudinary_public_id=result["public_id"],
            user_id=(owner_user.id if owner_user else None),
            guest_id=(owner_guest if owner_guest and not owner_user else None)
        )

        # Add main file record
        try:
            db.add(uploaded)
            db.commit()
            db.refresh(uploaded)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"DB commit failed for UploadedFile: {str(e)}")
            
        # Save rows
        try:
            for _, row in df.iterrows():
                row_dict = row.to_dict()
                safe_row = clean_json(row_dict)   # sanitize floats
                db.add(models.FileRow(file_id=uploaded.id, data=safe_row))
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"DB commit failed for FileRow: {str(e)}")

        return {
            "id": uploaded.id,
            "filename": uploaded.filename,
            "rows": uploaded.total_rows,
            "columns": uploaded.total_columns,
            "cloudinary_url": uploaded.cloudinary_url,
            "public_id": uploaded.cloudinary_public_id,
            "owner": owner_user.email if owner_user else f"guest:{owner_guest}",
        }

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error("Upload-file failed:\n%s", tb)  # Logs full traceback to console
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/files")
def list_uploads(identity = Depends(get_identity), db: Session = Depends(get_db)):
    if identity["user"]:
        files = db.query(models.UploadedFile).filter(models.UploadedFile.user_id == identity["user"].id).all()
    else:
        files = db.query(models.UploadedFile).filter(models.UploadedFile.guest_id == identity["guest_id"]).all()
    
    # ✅ Convert ORM objects to plain dicts without binary data
    result = []
    for f in files:
        result.append({
            "id": f.id,
            "name": f.filename,
            "uploadedAt": f.uploaded_at.isoformat() if f.uploaded_at else None,
            "size": getattr(f, "size", None),
            "contentType": getattr(f, "content_type", None)
        })
    
    return {"files": result}

@router.get("/files/{file_id}/download")
def download_file(file_id: int, identity: dict = Depends(get_identity), db: Session = Depends(get_db)) -> Any:
    """Return a secure Cloudinary download URL for the user's file."""
    user = identity.get("user")
    guest_id = identity.get("guest_id")

    file = db.query(models.UploadedFile).filter(models.UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # Check ownership
    if user and file.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized to access this file")
    if not user and file.guest_id != guest_id:
        raise HTTPException(status_code=403, detail="Unauthorized to access this file")

    if not file.cloudinary_url:
        raise HTTPException(status_code=400, detail="File has no Cloudinary URL")

    # Optional: could generate a time-limited signed URL if needed
    return {"download_url": file.cloudinary_url, "filename": file.filename}