import os
import io
import hashlib
import uuid
from typing import Optional, List, Tuple
from pathlib import Path
import PyPDF2
from PIL import Image
import pytesseract
from sentence_transformers import SentenceTransformer
import numpy as np
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.models.document import DocumentCreate, DocumentResponse, FileType, DocumentStatus

class DocumentProcessor:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)
    
    async def process_document(self, file_content: bytes, filename: str, db_session: AsyncSession) -> DocumentResponse:
        """Process uploaded document and store in database"""
        try:
            # Determine file type
            file_type = self._get_file_type(filename)
            
            # Save file
            file_path = await self._save_file(file_content, filename)
            
            # Extract text content
            content = await self._extract_text(file_content, file_type)
            
            # Generate content hash
            content_hash = self._generate_content_hash(content) if content else None
            
            # Create document record
            document_id = str(uuid.uuid4())
            document_data = DocumentCreate(
                filename=filename,
                file_type=file_type,
                file_size=len(file_content),
                content=content,
                content_hash=content_hash
            )
            
            # Store in database
            await self._store_document(db_session, document_id, document_data, str(file_path))
            
            # Generate embeddings asynchronously
            asyncio.create_task(self._generate_embeddings(document_id, content, db_session))
            
            return DocumentResponse(
                id=document_id,
                filename=filename,
                file_path=str(file_path),
                file_type=file_type,
                file_size=len(file_content),
                content=content,
                content_hash=content_hash,
                status=DocumentStatus.PROCESSING,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
        except Exception as e:
            raise Exception(f"Failed to process document: {str(e)}")
    
    def _get_file_type(self, filename: str) -> FileType:
        """Determine file type from filename"""
        ext = Path(filename).suffix.lower()
        if ext == '.pdf':
            return FileType.PDF
        elif ext == '.txt':
            return FileType.TXT
        elif ext in ['.png', '.jpg', '.jpeg']:
            return FileType(ext[1:])
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    
    async def _save_file(self, file_content: bytes, filename: str) -> Path:
        """Save uploaded file to disk"""
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = self.upload_dir / unique_filename
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return file_path
    
    async def _extract_text(self, file_content: bytes, file_type: FileType) -> Optional[str]:
        """Extract text content from different file types"""
        try:
            if file_type == FileType.PDF:
                return await self._extract_pdf_text(file_content)
            elif file_type == FileType.TXT:
                return file_content.decode('utf-8')
            elif file_type in [FileType.PNG, FileType.JPG, FileType.JPEG]:
                return await self._extract_image_text(file_content)
            else:
                return None
        except Exception as e:
            print(f"Error extracting text from {file_type}: {e}")
            return None
    
    async def _extract_pdf_text(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text_content = ""
            
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
            
            return text_content.strip()
        except Exception as e:
            raise Exception(f"Failed to extract PDF text: {str(e)}")
    
    async def _extract_image_text(self, file_content: bytes) -> str:
        """Extract text from image using OCR"""
        try:
            image = Image.open(io.BytesIO(file_content))
            text_content = pytesseract.image_to_string(image)
            return text_content.strip()
        except Exception as e:
            raise Exception(f"Failed to extract image text: {str(e)}")
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate SHA-256 hash of content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    async def _store_document(self, db_session: AsyncSession, document_id: str, 
                            document_data: DocumentCreate, file_path: str):
        """Store document in database"""
        query = text("""
            INSERT INTO documents (id, filename, file_path, file_type, file_size, content, content_hash)
            VALUES (:id, :filename, :file_path, :file_type, :file_size, :content, :content_hash)
        """)
        
        await db_session.execute(query, {
            "id": document_id,
            "filename": document_data.filename,
            "file_path": file_path,
            "file_type": document_data.file_type.value,
            "file_size": document_data.file_size,
            "content": document_data.content,
            "content_hash": document_data.content_hash
        })
        
        await db_session.commit()
    
    async def _generate_embeddings(self, document_id: str, content: str, db_session: AsyncSession):
        """Generate and store document embeddings"""
        try:
            if not content:
                return
            
            # Generate embedding
            embedding = self.embedding_model.encode(content)
            embedding_list = embedding.tolist()
            
            # Store embedding in database
            embedding_id = str(uuid.uuid4())
            query = text("""
                INSERT INTO document_embeddings (id, document_id, embedding_vector, embedding_model)
                VALUES (:id, :document_id, :embedding_vector, :embedding_model)
            """)
            
            await db_session.execute(query, {
                "id": embedding_id,
                "document_id": document_id,
                "embedding_vector": str(embedding_list),
                "embedding_model": "all-MiniLM-L6-v2"
            })
            
            # Update document status to completed
            update_query = text("""
                UPDATE documents 
                SET status = 'completed', updated_at = CURRENT_TIMESTAMP
                WHERE id = :document_id
            """)
            
            await db_session.execute(update_query, {"document_id": document_id})
            await db_session.commit()
            
        except Exception as e:
            print(f"Error generating embeddings for document {document_id}: {e}")
            # Update document status to failed
            try:
                update_query = text("""
                    UPDATE documents 
                    SET status = 'failed', updated_at = CURRENT_TIMESTAMP
                    WHERE id = :document_id
                """)
                await db_session.execute(update_query, {"document_id": document_id})
                await db_session.commit()
            except:
                pass
    
    async def get_document_status(self, document_id: str, db_session: AsyncSession) -> DocumentStatus:
        """Get document processing status"""
        query = text("SELECT status FROM documents WHERE id = :document_id")
        result = await db_session.execute(query, {"document_id": document_id})
        row = result.fetchone()
        
        if row:
            return DocumentStatus(row[0])
        else:
            raise ValueError(f"Document {document_id} not found")
    
    async def get_document_content(self, document_id: str, db_session: AsyncSession) -> Optional[str]:
        """Get document content"""
        query = text("SELECT content FROM documents WHERE id = :document_id")
        result = await db_session.execute(query, {"document_id": document_id})
        row = result.fetchone()
        
        return row[0] if row else None

# Global document processor instance
document_processor = DocumentProcessor()
