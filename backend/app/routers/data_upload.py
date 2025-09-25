# app/routers/upload.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app import models
from app.database import get_db
import pandas as pd
from io import BytesIO
import cloudinary
import cloudinary.uploader
import time
import re
import traceback
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# store the data only data base

# @router.post("/upload-file/")
# async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    
#     # Read raw file bytes (for safe storage)
#     raw_bytes = await file.read()

#     # Reset pointer for pandas
#     buffer = BytesIO(raw_bytes)

#     # Parse with pandas
#     if file.filename.endswith(".csv"):
#         df = pd.read_csv(buffer)
#     else:
#         df = pd.read_excel(buffer)

#     # Clean / normalize
#     df = df.dropna(how="all")  
#     df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
#     # Ensure JSON-safe values (Postgres JSON doesn't allow NaN/NaT)
#     df = df.where(pd.notnull(df), None)

#     # Create UploadedFile entry
#     uploaded = models.UploadedFile(
#         filename=file.filename,
#         file_type=file.content_type,
#         total_rows=len(df),
#         total_columns=len(df.columns),
#         file_data=raw_bytes,
#     )
#     db.add(uploaded)
#     db.commit()
#     db.refresh(uploaded)

#     # Save schema (column metadata)
#     for col in df.columns:
#         db.add(models.FileColumn(file_id=uploaded.id, name=col, dtype=str(df[col].dtype)))

#     # Save rows as JSON
#     for _, row in df.iterrows():
#         db.add(models.FileRow(file_id=uploaded.id, data=row.to_dict()))

#     db.commit()
#     db.refresh(uploaded)

#     return {
#         "id": uploaded.id,
#         "filename": uploaded.filename,
#         "rows": uploaded.total_rows,
#         "columns": uploaded.total_columns
#     }

# storing the data in both the cloudinary and database

@router.post("/upload-file/")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Read file content
        file_content = await file.read()

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
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
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
            cloudinary_public_id=result["public_id"]
        )

        # Add main file record
        try:
            db.add(uploaded)
            db.commit()
            db.refresh(uploaded)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"DB commit failed for UploadedFile: {str(e)}")

        # Save columns metadata
        try:
            for col in df.columns:
                db.add(models.FileColumn(file_id=uploaded.id, name=col, dtype=str(df[col].dtype)))
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"DB commit failed for FileColumn: {str(e)}")

        # Save rows
        try:
            for _, row in df.iterrows():
                row_dict = row.to_dict()
                db.add(models.FileRow(file_id=uploaded.id, data=row_dict))
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
            "public_id": uploaded.cloudinary_public_id
        }

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error("Upload-file failed:\n%s", tb)  # Logs full traceback to console
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# store the data only in cloudinary

# @router.post("/upload-file/")
# async def upload_file_cloud_only(file: UploadFile = File(...)):
#     try:
#         # Read file content
#         file_content = await file.read()

#         # Sanitize filename for Cloudinary
#         public_id_safe = re.sub(r'[^A-Za-z0-9_-]', '_', file.filename)
#         public_id = f"{public_id_safe}_{int(time.time())}"

#         # Upload to Cloudinary as raw
#         file_buffer = BytesIO(file_content)
#         result = cloudinary.uploader.upload(
#             file_buffer,
#             resource_type="raw",
#             folder="uploads",
#             public_id=public_id
#         )

#         # Return Cloudinary info only
#         return {
#             "filename": file.filename,
#             "cloudinary_url": result.get("secure_url"),
#             "public_id": result.get("public_id"),
#             "bytes_size": len(file_content)
#         }

#     except Exception as e:
#         import traceback
#         tb = traceback.format_exc()
#         logger.error("Cloud-only upload failed:\n%s", tb)
#         raise HTTPException(status_code=500, detail=f"Cloud upload failed: {str(e)}")