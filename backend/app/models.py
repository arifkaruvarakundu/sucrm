# app/models.py
from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime, LargeBinary
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

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

    # relationships
    rows = relationship("FileRow", back_populates="file", cascade="all, delete-orphan")
    columns = relationship("FileColumn", back_populates="file", cascade="all, delete-orphan")


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
    data = Column(JSON, nullable=False)  # store row as JSON

    file = relationship("UploadedFile", back_populates="rows")
