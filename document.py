from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class FileType(str, Enum):
    PDF = "pdf"
    TXT = "txt"
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"

class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Base document model
class DocumentBase(BaseModel):
    filename: str = Field(..., description="Original filename")
    file_type: FileType = Field(..., description="File type")
    file_size: int = Field(..., description="File size in bytes")

# Document creation model
class DocumentCreate(DocumentBase):
    content: Optional[str] = Field(None, description="Extracted text content")
    content_hash: Optional[str] = Field(None, description="Content hash for deduplication")

# Document response model
class DocumentResponse(DocumentBase):
    id: str = Field(..., description="Unique document ID")
    file_path: str = Field(..., description="File storage path")
    content: Optional[str] = Field(None, description="Extracted text content")
    content_hash: Optional[str] = Field(None, description="Content hash")
    status: DocumentStatus = Field(..., description="Processing status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True

# Document with embeddings
class DocumentWithEmbedding(DocumentResponse):
    embedding_vector: Optional[List[float]] = Field(None, description="Document embedding vector")
    embedding_model: Optional[str] = Field(None, description="Embedding model used")

# Document search result
class DocumentSearchResult(BaseModel):
    id: str = Field(..., description="Document ID")
    filename: str = Field(..., description="Document filename")
    content: Optional[str] = Field(None, description="Document content")
    similarity_score: Optional[float] = Field(None, description="Similarity score for vector search")
    relevance_score: Optional[float] = Field(None, description="Relevance score for full-text search")
    created_at: datetime = Field(..., description="Document creation date")

# Document upload response
class DocumentUploadResponse(BaseModel):
    document: DocumentResponse = Field(..., description="Uploaded document details")
    message: str = Field(..., description="Upload status message")
    processing_id: Optional[str] = Field(None, description="Processing workflow ID")

# Document list response
class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse] = Field(..., description="List of documents")
    total_count: int = Field(..., description="Total number of documents")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    has_next: bool = Field(..., description="Whether there are more pages")

# Document processing status
class DocumentProcessingStatus(BaseModel):
    document_id: str = Field(..., description="Document ID")
    status: DocumentStatus = Field(..., description="Processing status")
    progress: float = Field(..., description="Processing progress (0-100)")
    message: Optional[str] = Field(None, description="Status message")
    error: Optional[str] = Field(None, description="Error message if failed")

# Document metadata
class DocumentMetadata(BaseModel):
    id: str = Field(..., description="Document ID")
    filename: str = Field(..., description="Document filename")
    file_type: FileType = Field(..., description="File type")
    file_size: int = Field(..., description="File size in bytes")
    word_count: Optional[int] = Field(None, description="Number of words in content")
    page_count: Optional[int] = Field(None, description="Number of pages (for PDFs)")
    language: Optional[str] = Field(None, description="Detected language")
    created_at: datetime = Field(..., description="Creation timestamp")
    tags: List[str] = Field(default_factory=list, description="Document tags")

# Document update model
class DocumentUpdate(BaseModel):
    filename: Optional[str] = Field(None, description="New filename")
    content: Optional[str] = Field(None, description="Updated content")
    tags: Optional[List[str]] = Field(None, description="Document tags")

# Document search request
class DocumentSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    search_type: str = Field(default="hybrid", description="Search type: vector, fulltext, or hybrid")
    limit: int = Field(default=10, description="Maximum number of results")
    threshold: float = Field(default=0.7, description="Similarity threshold for vector search")
    file_types: Optional[List[FileType]] = Field(None, description="Filter by file types")
    date_from: Optional[datetime] = Field(None, description="Filter by date from")
    date_to: Optional[datetime] = Field(None, description="Filter by date to")

# Document search response
class DocumentSearchResponse(BaseModel):
    results: List[DocumentSearchResult] = Field(..., description="Search results")
    total_count: int = Field(..., description="Total number of results")
    search_type: str = Field(..., description="Search type used")
    execution_time_ms: int = Field(..., description="Search execution time in milliseconds")
    query: str = Field(..., description="Original search query")

