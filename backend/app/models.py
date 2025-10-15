# app/models.py
from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime, LargeBinary, Boolean, Index, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import re

Base = declarative_base()

class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    total_rows = Column(Integer, nullable=False)
    total_columns = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # raw file storage (optional: can also store just a path)
    file_data = Column(LargeBinary, nullable=False)
    
    # Cloudinary storage fields
    cloudinary_url = Column(String, nullable=True)
    cloudinary_public_id = Column(String, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    guest_id = Column(UUID(as_uuid=False), ForeignKey("guests.id"), nullable=True)  # <-- MATCH TYPE

    # relationships
    rows = relationship("FileRow", back_populates="file", cascade="all, delete-orphan")
    columns = relationship("FileColumn", back_populates="file", cascade="all, delete-orphan")
    guest = relationship("Guest", backref="files")
    mappings = relationship("ColumnMapping", back_populates="file", cascade="all, delete-orphan")

class FileColumn(Base):
    __tablename__ = "file_columns"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("uploaded_files.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)
    dtype = Column(String, nullable=True)  # store pandas dtype

    file = relationship("UploadedFile", back_populates="columns")

class FileRow(Base):
    __tablename__ = "file_rows"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("uploaded_files.id", ondelete="CASCADE"))
    data = Column(JSONB, nullable=False)  # store row as JSON

    file = relationship("UploadedFile", back_populates="rows")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    user_type = Column(String, default="user")  # or "admin"

class Guest(Base):
    __tablename__ = "guests"
    # store as text/uuid string; using PG UUID type is cleaner if you use Postgres
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # optional retention policy

class ColumnMapping(Base):
    __tablename__ = "column_mappings"

    id = Column(Integer, primary_key=True, index=True)
    # if file_id is null → user-level default mapping for analysis_type
    file_id = Column(Integer, ForeignKey("uploaded_files.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    guest_id = Column(UUID(as_uuid=False), ForeignKey("guests.id"), nullable=True)

    analysis_type = Column(String, nullable=False)   # e.g. "order", "customer", "product"
    mapping = Column(JSON, nullable=False)           # e.g. {"orderId": "Order ID", ...}

    is_default = Column(Boolean, default=False)      # optional: true if it's a user-default mapping
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    file = relationship("UploadedFile", back_populates="mappings")
    user = relationship("User", backref="column_mappings")
    guest = relationship("Guest", backref="column_mappings")

    # helpful index to speed lookups; consider unique constraints in migration (see below)
    __table_args__ = (
        Index("ix_column_mappings_file_user_analysis", "file_id", "user_id", "analysis_type"),
    )

class WhatsAppTemplate(Base):
    __tablename__ = "whatsapp_templates"

    id = Column(Integer, primary_key=True, index=True)
    template_name = Column(String, unique=True, index=True, nullable=False)
    category = Column(String(100))
    language = Column(String(10))
    status = Column(String(50))
    body = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def variables(self) -> list[str]:
        return re.findall(r"{{.*?}}", self.body or "")

