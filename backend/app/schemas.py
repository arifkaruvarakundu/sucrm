# app/schemas.py
from pydantic import BaseModel
from typing import List, Dict, Any

class FileRowBase(BaseModel):
    data: Dict[str, Any]

class FileRowCreate(FileRowBase):
    pass

class FileRow(FileRowBase):
    id: int
    class Config:
        orm_mode = True


class UploadedFileBase(BaseModel):
    filename: str
    file_type: str
    total_rows: int
    total_columns: int

class UploadedFileCreate(UploadedFileBase):
    rows: List[FileRowCreate]

class UploadedFile(UploadedFileBase):
    id: int
    rows: List[FileRow] = []
    class Config:
        orm_mode = True
