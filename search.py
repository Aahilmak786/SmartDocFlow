from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import time
import uuid
from sentence_transformers import SentenceTransformer

from app.core.database import get_db, search_similar_documents, full_text_search
from app.models.document import DocumentSearchRequest, DocumentSearchResponse, DocumentSearchResult
from app.core.config import settings

router = APIRouter()

# Initialize embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

@router.post("/", response_model=DocumentSearchResponse)
async def search_documents(
    request: DocumentSearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """Search documents using vector search, full-text search, or hybrid approach"""
    start_time = time.time()
    
    try:
        results = []
        search_type = request.search_type.lower()
        
        if search_type == "vector":
            results = await _vector_search(request.query, request.limit, request.threshold, db)
        elif search_type == "fulltext":
            results = await _fulltext_search(request.query, request.limit, db)
        elif search_type == "hybrid":
            results = await _hybrid_search(request.query, request.limit, request.threshold, db)
        else:
            raise HTTPException(status_code=400, detail="Invalid search type. Use 'vector', 'fulltext', or 'hybrid'")
        
        # Apply additional filters
        if request.file_types:
            results = [r for r in results if r.file_type in request.file_types]
        
        if request.date_from or request.date_to:
            results = _filter_by_date(results, request.date_from, request.date_to)
        
        # Log search
        execution_time_ms = int((time.time() - start_time) * 1000)
        await _log_search(request.query, search_type, len(results), execution_time_ms, db)
        
        return DocumentSearchResponse(
            results=results[:request.limit],
            total_count=len(results),
            search_type=search_type,
            execution_time_ms=execution_time_ms,
            query=request.query
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/vector")
async def vector_search(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    threshold: float = Query(0.7, ge=0.0, le=1.0, description="Similarity threshold"),
    db: AsyncSession = Depends(get_db)
):
    """Vector search for similar documents"""
    try:
        results = await _vector_search(query, limit, threshold, db)
        return {
            "results": results,
            "total_count": len(results),
            "search_type": "vector",
            "query": query
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fulltext")
async def fulltext_search(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db)
):
    """Full-text search in document content"""
    try:
        results = await _fulltext_search(query, limit, db)
        return {
            "results": results,
            "total_count": len(results),
            "search_type": "fulltext",
            "query": query
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/similar/{document_id}")
async def find_similar_documents(
    document_id: str,
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    threshold: float = Query(0.7, ge=0.0, le=1.0, description="Similarity threshold"),
    db: AsyncSession = Depends(get_db)
):
    """Find documents similar to a specific document"""
    try:
        # Get the target document's embedding
        query = """
            SELECT de.embedding_vector
            FROM document_embeddings de
            WHERE de.document_id = :document_id
        """
        result = await db.execute(query, {"document_id": document_id})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Document not found or no embedding available")
        
        # Parse embedding vector
        embedding_str = row[0]
        embedding_vector = eval(embedding_str)  # Convert string representation back to list
        
        # Search for similar documents
        similar_docs = await search_similar_documents(embedding_vector, limit, threshold)
        
        results = []
        for doc in similar_docs:
            results.append(DocumentSearchResult(
                id=doc[0],
                filename=doc[1],
                content=doc[2][:500] + "..." if len(doc[2]) > 500 else doc[2],  # Truncate content
                similarity_score=1 - doc[4],  # Convert distance to similarity
                created_at=doc[5] if len(doc) > 5 else None
            ))
        
        return {
            "results": results,
            "total_count": len(results),
            "search_type": "vector",
            "reference_document_id": document_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def _vector_search(query: str, limit: int, threshold: float, db: AsyncSession) -> List[DocumentSearchResult]:
    """Perform vector search"""
    # Generate embedding for the query
    query_embedding = embedding_model.encode(query)
    query_embedding_list = query_embedding.tolist()
    
    # Search for similar documents
    similar_docs = await search_similar_documents(query_embedding_list, limit, threshold)
    
    results = []
    for doc in similar_docs:
        results.append(DocumentSearchResult(
            id=doc[0],
            filename=doc[1],
            content=doc[2][:500] + "..." if len(doc[2]) > 500 else doc[2],
            similarity_score=1 - doc[4],  # Convert distance to similarity
            created_at=doc[5] if len(doc) > 5 else None
        ))
    
    return results

async def _fulltext_search(query: str, limit: int, db: AsyncSession) -> List[DocumentSearchResult]:
    """Perform full-text search"""
    # Search in document content
    search_results = await full_text_search(query, limit)
    
    results = []
    for doc in search_results:
        results.append(DocumentSearchResult(
            id=doc[0],
            filename=doc[1],
            content=doc[2][:500] + "..." if len(doc[2]) > 500 else doc[2],
            relevance_score=doc[3],
            created_at=doc[4] if len(doc) > 4 else None
        ))
    
    return results

async def _hybrid_search(query: str, limit: int, threshold: float, db: AsyncSession) -> List[DocumentSearchResult]:
    """Perform hybrid search combining vector and full-text search"""
    # Get vector search results
    vector_results = await _vector_search(query, limit * 2, threshold, db)
    
    # Get full-text search results
    fulltext_results = await _fulltext_search(query, limit * 2, db)
    
    # Combine and rank results
    combined_results = {}
    
    # Add vector search results
    for result in vector_results:
        combined_results[result.id] = {
            "result": result,
            "vector_score": result.similarity_score or 0,
            "fulltext_score": 0
        }
    
    # Add full-text search results
    for result in fulltext_results:
        if result.id in combined_results:
            combined_results[result.id]["fulltext_score"] = result.relevance_score or 0
        else:
            combined_results[result.id] = {
                "result": result,
                "vector_score": 0,
                "fulltext_score": result.relevance_score or 0
            }
    
    # Calculate hybrid scores and sort
    hybrid_results = []
    for doc_id, scores in combined_results.items():
        hybrid_score = (scores["vector_score"] * 0.6) + (scores["fulltext_score"] * 0.4)
        result = scores["result"]
        result.similarity_score = hybrid_score
        hybrid_results.append((result, hybrid_score))
    
    # Sort by hybrid score and return top results
    hybrid_results.sort(key=lambda x: x[1], reverse=True)
    return [result[0] for result in hybrid_results[:limit]]

def _filter_by_date(results: List[DocumentSearchResult], date_from, date_to) -> List[DocumentSearchResult]:
    """Filter results by date range"""
    filtered_results = []
    
    for result in results:
        if result.created_at:
            if date_from and result.created_at < date_from:
                continue
            if date_to and result.created_at > date_to:
                continue
            filtered_results.append(result)
    
    return filtered_results

async def _log_search(query: str, search_type: str, results_count: int, execution_time_ms: int, db: AsyncSession):
    """Log search operation"""
    try:
        log_id = str(uuid.uuid4())
        query = """
            INSERT INTO search_logs (id, query, search_type, results_count, execution_time_ms)
            VALUES (:id, :query, :search_type, :results_count, :execution_time_ms)
        """
        
        await db.execute(query, {
            "id": log_id,
            "query": query,
            "search_type": search_type,
            "results_count": results_count,
            "execution_time_ms": execution_time_ms
        })
        
        await db.commit()
    except Exception as e:
        print(f"Failed to log search: {e}")
        # Don't raise exception for logging failures


