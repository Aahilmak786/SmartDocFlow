from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.core.database import get_db
from app.services.workflow_orchestrator import workflow_orchestrator
from app.services.external_actions import ExternalActionService

router = APIRouter()

class WorkflowConfig(BaseModel):
    enable_ai_analysis: bool = True
    analysis_type: str = "general"
    enable_notifications: bool = False
    notification_channels: List[str] = []

class SearchWorkflowRequest(BaseModel):
    query: str
    search_type: str = "hybrid"
    analysis_type: str = "general"
    enable_notifications: bool = True

class BatchAnalysisRequest(BaseModel):
    document_ids: List[str]
    analysis_type: str = "general"
    enable_notifications: bool = True

class IntelligentRoutingRequest(BaseModel):
    enable_legal_routing: bool = True
    enable_financial_routing: bool = True
    enable_calendar_events: bool = True

@router.post("/document-processing")
async def execute_document_processing_workflow(
    file: UploadFile = File(...),
    config: Optional[WorkflowConfig] = None,
    db: AsyncSession = Depends(get_db)
):
    """Execute complete document processing workflow with AI analysis and notifications"""
    try:
        # Read file content
        file_content = await file.read()
        
        # Execute workflow
        result = await workflow_orchestrator.execute_document_processing_workflow(
            file_content, file.filename, db, config.dict() if config else None
        )
        
        return {
            "message": "Document processing workflow completed successfully",
            "workflow_id": result["workflow_id"],
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search-and-analyze")
async def execute_search_and_analyze_workflow(
    request: SearchWorkflowRequest,
    db: AsyncSession = Depends(get_db)
):
    """Execute search and analysis workflow"""
    try:
        result = await workflow_orchestrator.execute_search_and_analyze_workflow(
            request.query, request.search_type, request.analysis_type, db
        )
        
        return {
            "message": "Search and analysis workflow completed successfully",
            "workflow_id": result["workflow_id"],
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-analysis")
async def execute_batch_analysis_workflow(
    request: BatchAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """Execute batch analysis workflow"""
    try:
        result = await workflow_orchestrator.execute_batch_analysis_workflow(
            request.document_ids, request.analysis_type, db
        )
        
        return {
            "message": "Batch analysis workflow completed successfully",
            "workflow_id": result["workflow_id"],
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/intelligent-routing")
async def execute_intelligent_routing_workflow(
    file: UploadFile = File(...),
    config: Optional[IntelligentRoutingRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    """Execute intelligent document routing workflow"""
    try:
        # Read file content
        file_content = await file.read()
        
        # Execute workflow
        result = await workflow_orchestrator.execute_intelligent_document_routing_workflow(
            file_content, file.filename, db
        )
        
        return {
            "message": "Intelligent routing workflow completed successfully",
            "workflow_id": result["workflow_id"],
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{workflow_id}")
async def get_workflow_status(
    workflow_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get workflow execution status"""
    try:
        from sqlalchemy import text
        
        query = text("""
            SELECT workflow_name, status, input_data, output_data, started_at, completed_at, execution_time_ms
            FROM workflow_executions
            WHERE id = :workflow_id
        """)
        
        result = await db.execute(query, {"workflow_id": workflow_id})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        import json
        
        return {
            "workflow_id": workflow_id,
            "workflow_name": row[0],
            "status": row[1],
            "input_data": json.loads(row[2]) if row[2] else None,
            "output_data": json.loads(row[3]) if row[3] else None,
            "started_at": row[4],
            "completed_at": row[5],
            "execution_time_ms": row[6]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/executions")
async def list_workflow_executions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    workflow_name: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List workflow executions with pagination and filtering"""
    try:
        from sqlalchemy import text
        
        offset = (page - 1) * page_size
        
        # Build query
        where_clause = "WHERE 1=1"
        params = {}
        
        if status:
            where_clause += " AND status = :status"
            params["status"] = status
        
        if workflow_name:
            where_clause += " AND workflow_name = :workflow_name"
            params["workflow_name"] = workflow_name
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM workflow_executions {where_clause}"
        count_result = await db.execute(count_query, params)
        total_count = count_result.scalar()
        
        # Get executions
        query = f"""
            SELECT id, workflow_name, status, started_at, completed_at, execution_time_ms
            FROM workflow_executions {where_clause}
            ORDER BY started_at DESC
            LIMIT :limit OFFSET :offset
        """
        
        params.update({"limit": page_size, "offset": offset})
        result = await db.execute(query, params)
        rows = result.fetchall()
        
        executions = []
        for row in rows:
            executions.append({
                "workflow_id": row[0],
                "workflow_name": row[1],
                "status": row[2],
                "started_at": row[3],
                "completed_at": row[4],
                "execution_time_ms": row[5]
            })
        
        return {
            "executions": executions,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "has_next": (page * page_size) < total_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/external-actions/{workflow_id}")
async def get_workflow_external_actions(
    workflow_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get external actions for a workflow execution"""
    try:
        from sqlalchemy import text
        
        query = text("""
            SELECT id, action_type, action_data, status, response_data, created_at, executed_at
            FROM external_actions
            WHERE workflow_execution_id = :workflow_id
            ORDER BY created_at DESC
        """)
        
        result = await db.execute(query, {"workflow_id": workflow_id})
        rows = result.fetchall()
        
        import json
        
        actions = []
        for row in rows:
            actions.append({
                "action_id": row[0],
                "action_type": row[1],
                "action_data": json.loads(row[2]) if row[2] else {},
                "status": row[3],
                "response_data": json.loads(row[4]) if row[4] else {},
                "created_at": row[5],
                "executed_at": row[6]
            })
        
        return {
            "workflow_id": workflow_id,
            "actions": actions,
            "total_actions": len(actions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-notification")
async def send_custom_notification(
    message: str = Query(..., description="Notification message"),
    channel: Optional[str] = Query(None, description="Slack channel (optional)"),
    workflow_id: str = Query(..., description="Workflow ID for tracking"),
    db: AsyncSession = Depends(get_db)
):
    """Send custom notification via Slack"""
    try:
        external_actions = ExternalActionService()
        result = await external_actions.send_slack_notification(
            message, workflow_id, db, channel
        )
        
        return {
            "message": "Notification sent successfully",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-calendar-event")
async def create_custom_calendar_event(
    title: str = Query(..., description="Event title"),
    description: str = Query(..., description="Event description"),
    workflow_id: str = Query(..., description="Workflow ID for tracking"),
    db: AsyncSession = Depends(get_db)
):
    """Create custom calendar event"""
    try:
        external_actions = ExternalActionService()
        result = await external_actions.create_calendar_event(
            title, description, workflow_id, db
        )
        
        return {
            "message": "Calendar event created successfully",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflow-types")
async def get_available_workflow_types():
    """Get available workflow types"""
    return {
        "workflow_types": [
            {
                "id": "document_processing",
                "name": "Document Processing",
                "description": "Complete document processing with AI analysis and notifications",
                "steps": [
                    "Document upload and text extraction",
                    "Vector embedding generation",
                    "AI content analysis",
                    "Slack notifications (optional)"
                ]
            },
            {
                "id": "search_and_analyze",
                "name": "Search and Analyze",
                "description": "Search documents and extract insights using AI",
                "steps": [
                    "Vector/full-text search",
                    "AI insight extraction",
                    "Document summarization",
                    "Notification with results"
                ]
            },
            {
                "id": "batch_analysis",
                "name": "Batch Analysis",
                "description": "Analyze multiple documents and compare them",
                "steps": [
                    "Document content retrieval",
                    "AI document comparison",
                    "Summary generation",
                    "Comprehensive notification"
                ]
            },
            {
                "id": "intelligent_routing",
                "name": "Intelligent Routing",
                "description": "Automatically route documents based on content analysis",
                "steps": [
                    "Document processing and analysis",
                    "Content-based routing decisions",
                    "Team notifications",
                    "Calendar event creation (optional)"
                ]
            }
        ]
    }


