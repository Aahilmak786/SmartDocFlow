import pymysql
import asyncio
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.config import settings

# Database URL
DATABASE_URL = f"mysql+pymysql://{settings.TIDB_USER}:{settings.TIDB_PASSWORD}@{settings.TIDB_HOST}:{settings.TIDB_PORT}/{settings.TIDB_DATABASE}"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

# Create session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db() -> AsyncSession:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        # Create documents table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS documents (
                id VARCHAR(36) PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                file_type VARCHAR(50) NOT NULL,
                file_size BIGINT NOT NULL,
                content TEXT,
                content_hash VARCHAR(64),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_filename (filename),
                INDEX idx_file_type (file_type),
                INDEX idx_created_at (created_at)
            )
        """))
        
        # Create document_embeddings table for vector search
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS document_embeddings (
                id VARCHAR(36) PRIMARY KEY,
                document_id VARCHAR(36) NOT NULL,
                embedding_vector JSON NOT NULL,
                embedding_model VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                INDEX idx_document_id (document_id),
                INDEX idx_embedding_model (embedding_model)
            )
        """))
        
        # Create search_logs table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS search_logs (
                id VARCHAR(36) PRIMARY KEY,
                query TEXT NOT NULL,
                search_type ENUM('vector', 'fulltext', 'hybrid') NOT NULL,
                results_count INT NOT NULL,
                execution_time_ms INT NOT NULL,
                user_id VARCHAR(36),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_search_type (search_type),
                INDEX idx_created_at (created_at)
            )
        """))
        
        # Create workflow_executions table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS workflow_executions (
                id VARCHAR(36) PRIMARY KEY,
                workflow_name VARCHAR(100) NOT NULL,
                document_id VARCHAR(36),
                status ENUM('pending', 'running', 'completed', 'failed') NOT NULL,
                input_data JSON,
                output_data JSON,
                error_message TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP NULL,
                execution_time_ms INT,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL,
                INDEX idx_workflow_name (workflow_name),
                INDEX idx_status (status),
                INDEX idx_started_at (started_at)
            )
        """))
        
        # Create external_actions table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS external_actions (
                id VARCHAR(36) PRIMARY KEY,
                workflow_execution_id VARCHAR(36) NOT NULL,
                action_type ENUM('slack_notification', 'calendar_event', 'email', 'webhook') NOT NULL,
                action_data JSON NOT NULL,
                status ENUM('pending', 'sent', 'failed') NOT NULL,
                response_data JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                executed_at TIMESTAMP NULL,
                FOREIGN KEY (workflow_execution_id) REFERENCES workflow_executions(id) ON DELETE CASCADE,
                INDEX idx_action_type (action_type),
                INDEX idx_status (status)
            )
        """))
        
        print("✅ Database tables initialized successfully!")

async def test_connection():
    """Test database connection"""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

# Vector search functions
async def search_similar_documents(embedding_vector: list, limit: int = 10, threshold: float = 0.7):
    """Search for similar documents using vector similarity"""
    async with engine.begin() as conn:
        # Convert embedding to JSON string for TiDB
        embedding_json = str(embedding_vector)
        
        query = text("""
            SELECT 
                d.id,
                d.filename,
                d.content,
                JSON_EXTRACT(de.embedding_vector, '$') as embedding,
                JSON_EXTRACT(de.embedding_vector, '$') <-> :embedding as distance
            FROM documents d
            JOIN document_embeddings de ON d.id = de.document_id
            WHERE JSON_EXTRACT(de.embedding_vector, '$') <-> :embedding < :threshold
            ORDER BY distance ASC
            LIMIT :limit
        """)
        
        result = await conn.execute(query, {
            "embedding": embedding_json,
            "threshold": threshold,
            "limit": limit
        })
        
        return result.fetchall()

async def full_text_search(query: str, limit: int = 10):
    """Perform full-text search on document content"""
    async with engine.begin() as conn:
        sql_query = text("""
            SELECT 
                id,
                filename,
                content,
                MATCH(content) AGAINST(:query IN NATURAL LANGUAGE MODE) as relevance_score
            FROM documents
            WHERE MATCH(content) AGAINST(:query IN NATURAL LANGUAGE MODE)
            ORDER BY relevance_score DESC
            LIMIT :limit
        """)
        
        result = await conn.execute(sql_query, {
            "query": query,
            "limit": limit
        })
        
        return result.fetchall()

