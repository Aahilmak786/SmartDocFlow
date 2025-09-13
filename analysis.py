from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.services.ai_analyzer import ai_analyzer
from app.services.document_processor import document_processor
from app.models.document import DocumentSearchResult

router = APIRouter()

class AnalysisRequest(BaseModel):
    document_id: str
    analysis_type: str = "general"  # general, legal, financial, technical

class ComparisonRequest(BaseModel):
    document_ids: List[str]
    comparison_type: str = "general"

class SummaryRequest(BaseModel):
    document_ids: List[str]
    summary_type: str = "executive"  # executive, detailed, actionable, technical

class SearchInsightsRequest(BaseModel):
    query: str
    search_type: str = "hybrid"
    limit: int = 10

@router.post("/document")
async def analyze_document(
    request: AnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """Analyze a single document using AI"""
    try:
        # Get document content
        content = await document_processor.get_document_content(request.document_id, db)
        
        if not content:
            raise HTTPException(status_code=404, detail="Document not found or no content available")
        
        # Perform AI analysis
        analysis = await ai_analyzer.analyze_document_content(content, request.analysis_type)
        
        if "error" in analysis:
            raise HTTPException(status_code=500, detail=analysis["error"])
        
        return {
            "document_id": request.document_id,
            "analysis_type": request.analysis_type,
            "analysis": analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare")
async def compare_documents(
    request: ComparisonRequest,
    db: AsyncSession = Depends(get_db)
):
    """Compare multiple documents using AI"""
    try:
        if len(request.document_ids) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 documents to compare")
        
        # Get document contents
        documents = []
        for doc_id in request.document_ids[:5]:  # Limit to 5 documents
            content = await document_processor.get_document_content(doc_id, db)
            if content:
                # Create a mock DocumentSearchResult for comparison
                doc_result = DocumentSearchResult(
                    id=doc_id,
                    filename=f"Document {doc_id[:8]}",
                    content=content,
                    created_at=None
                )
                documents.append(doc_result)
        
        if len(documents) < 2:
            raise HTTPException(status_code=400, detail="Not enough documents with content for comparison")
        
        # Perform AI comparison
        comparison = await ai_analyzer.compare_documents(documents)
        
        if "error" in comparison:
            raise HTTPException(status_code=500, detail=comparison["error"])
        
        return {
            "document_ids": request.document_ids,
            "comparison_type": request.comparison_type,
            "comparison": comparison
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summary")
async def generate_summary(
    request: SummaryRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate summary of multiple documents using AI"""
    try:
        if not request.document_ids:
            raise HTTPException(status_code=400, detail="No document IDs provided")
        
        # Get document contents
        documents = []
        for doc_id in request.document_ids[:10]:  # Limit to 10 documents
            content = await document_processor.get_document_content(doc_id, db)
            if content:
                # Create a mock DocumentSearchResult for summarization
                doc_result = DocumentSearchResult(
                    id=doc_id,
                    filename=f"Document {doc_id[:8]}",
                    content=content,
                    created_at=None
                )
                documents.append(doc_result)
        
        if not documents:
            raise HTTPException(status_code=400, detail="No documents with content found")
        
        # Generate AI summary
        summary = await ai_analyzer.generate_summary(documents, request.summary_type)
        
        if "error" in summary:
            raise HTTPException(status_code=500, detail=summary["error"])
        
        return {
            "document_ids": request.document_ids,
            "summary_type": request.summary_type,
            "summary": summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search-insights")
async def extract_search_insights(
    request: SearchInsightsRequest,
    db: AsyncSession = Depends(get_db)
):
    """Extract insights from search results using AI"""
    try:
        # Perform search first
        from app.api.routes.search import _vector_search, _fulltext_search, _hybrid_search
        
        search_results = []
        if request.search_type == "vector":
            search_results = await _vector_search(request.query, request.limit, 0.7, db)
        elif request.search_type == "fulltext":
            search_results = await _fulltext_search(request.query, request.limit, db)
        elif request.search_type == "hybrid":
            search_results = await _hybrid_search(request.query, request.limit, 0.7, db)
        else:
            raise HTTPException(status_code=400, detail="Invalid search type")
        
        if not search_results:
            return {
                "query": request.query,
                "search_type": request.search_type,
                "insights": {"message": "No search results to analyze"}
            }
        
        # Extract insights from search results
        insights = await ai_analyzer.extract_insights(search_results)
        
        if "error" in insights:
            raise HTTPException(status_code=500, detail=insights["error"])
        
        return {
            "query": request.query,
            "search_type": request.search_type,
            "search_results_count": len(search_results),
            "insights": insights
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/document/{document_id}/quick-analysis")
async def quick_analyze_document(
    document_id: str,
    analysis_type: str = Query("general", description="Analysis type: general, legal, financial, technical"),
    db: AsyncSession = Depends(get_db)
):
    """Quick analysis of a document"""
    try:
        # Get document content
        content = await document_processor.get_document_content(document_id, db)
        
        if not content:
            raise HTTPException(status_code=404, detail="Document not found or no content available")
        
        # Truncate content for quick analysis
        if len(content) > 2000:
            content = content[:2000] + "..."
        
        # Perform quick AI analysis
        analysis = await ai_analyzer.analyze_document_content(content, analysis_type)
        
        if "error" in analysis:
            raise HTTPException(status_code=500, detail=analysis["error"])
        
        return {
            "document_id": document_id,
            "analysis_type": analysis_type,
            "content_preview": content[:500] + "..." if len(content) > 500 else content,
            "analysis": analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/batch-analysis")
async def batch_analyze_documents(
    document_ids: str = Query(..., description="Comma-separated list of document IDs"),
    analysis_type: str = Query("general", description="Analysis type"),
    db: AsyncSession = Depends(get_db)
):
    """Batch analyze multiple documents"""
    try:
        doc_ids = [id.strip() for id in document_ids.split(",")]
        
        if len(doc_ids) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 documents allowed for batch analysis")
        
        results = []
        for doc_id in doc_ids:
            try:
                content = await document_processor.get_document_content(doc_id, db)
                if content:
                    # Truncate content for batch processing
                    if len(content) > 1500:
                        content = content[:1500] + "..."
                    
                    analysis = await ai_analyzer.analyze_document_content(content, analysis_type)
                    
                    results.append({
                        "document_id": doc_id,
                        "status": "success",
                        "analysis": analysis
                    })
                else:
                    results.append({
                        "document_id": doc_id,
                        "status": "error",
                        "error": "No content available"
                    })
            except Exception as e:
                results.append({
                    "document_id": doc_id,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "analysis_type": analysis_type,
            "total_documents": len(doc_ids),
            "successful_analyses": len([r for r in results if r["status"] == "success"]),
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis-types")
async def get_analysis_types():
    """Get available analysis types"""
    return {
        "analysis_types": [
            {
                "id": "general",
                "name": "General Analysis",
                "description": "General document analysis with topics, entities, and insights"
            },
            {
                "id": "legal",
                "name": "Legal Analysis",
                "description": "Legal document analysis with parties, terms, and implications"
            },
            {
                "id": "financial",
                "name": "Financial Analysis",
                "description": "Financial document analysis with figures, metrics, and trends"
            },
            {
                "id": "technical",
                "name": "Technical Analysis",
                "description": "Technical document analysis with technologies and requirements"
            }
        ]
    }


