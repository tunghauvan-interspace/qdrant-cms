from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Table, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# Association table for document tags
document_tags = Table(
    'document_tags',
    Base.metadata,
    Column('document_id', Integer, ForeignKey('documents.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    description = Column(Text, nullable=True)
    is_public = Column(String, default="private")  # public, private, restricted
    last_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)
    
    owner = relationship("User", back_populates="documents")
    tags = relationship("Tag", secondary=document_tags, back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    shares = relationship("DocumentShare", back_populates="document", cascade="all, delete-orphan")
    analytics = relationship("DocumentAnalytics", back_populates="document", cascade="all, delete-orphan")
    favorites = relationship("DocumentFavorite", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    qdrant_point_id = Column(String, nullable=False, unique=True)
    
    document = relationship("Document", back_populates="chunks")


class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    
    documents = relationship("Document", secondary=document_tags, back_populates="tags")


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(String, default="false")  # true, false
    created_at = Column(DateTime, default=datetime.utcnow)
    
    documents = relationship("Document", back_populates="owner")
    shared_documents = relationship("DocumentShare", back_populates="user")
    favorites = relationship("DocumentFavorite", back_populates="user")


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    version_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    tags_snapshot = Column(JSON, nullable=True)  # Store tags at version time
    is_public_snapshot = Column(String, nullable=False)
    file_path = Column(String, nullable=True)  # Path to versioned file if stored
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    change_summary = Column(Text, nullable=True)
    
    document = relationship("Document", back_populates="versions")
    created_by = relationship("User", foreign_keys=[created_by_id])


class DocumentShare(Base):
    __tablename__ = "document_shares"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    permission = Column(String, nullable=False)  # view, edit, admin
    shared_at = Column(DateTime, default=datetime.utcnow)
    shared_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    document = relationship("Document", back_populates="shares")
    user = relationship("User", back_populates="shared_documents", foreign_keys=[user_id])
    shared_by = relationship("User", foreign_keys=[shared_by_id])


class DocumentAnalytics(Base):
    __tablename__ = "document_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Null for anonymous
    action = Column(String, nullable=False)  # view, download, search_hit
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    action_metadata = Column(JSON, nullable=True)  # Additional context
    
    document = relationship("Document", back_populates="analytics")
    user = relationship("User", foreign_keys=[user_id])


class DocumentFavorite(Base):
    __tablename__ = "document_favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    document = relationship("Document", back_populates="favorites")
    user = relationship("User", back_populates="favorites")
