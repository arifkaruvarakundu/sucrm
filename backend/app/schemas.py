# app/schemas.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

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

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    user_type: str

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

class FileResponse(BaseModel):
    id: int
    name: str
    uploadedAt: datetime | None = None
    size: int | None = None
    contentType: str | None = None

class WhatsAppTemplateBase(BaseModel):
    template_name: str
    category: str | None = None
    language: str
    status: str
    body: str | None = None
    updated_at: datetime

    class Config:
        orm_mode = True

# class SendMessageRequest(BaseModel):
#     users: List[int]
#     templates: List[str]
#     variables: Optional[Dict[int, List[str]]] = None 

class SendMessageRequest(BaseModel):
    customers: Optional[List[int]]
    templates: Optional[List[str]]
    variables: Optional[Dict[int, List[str]]] = None