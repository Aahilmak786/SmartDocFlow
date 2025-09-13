import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json

from app.core.config import settings
from app.services.document_processor import document_processor
from app.services.ai_analyzer import ai_analyzer
from app.services.external_actions import ExternalActionService

class WorkflowOrchestrator:
    def __init__(self):
        self.external_actions = ExternalActionService()
    
    async def execute_document_processing_workflow(
        self, 
        file_content: bytes, 
        filename: str, 
        db_session: AsyncSession,
        workflow_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute complete document processing workflow"""
        workflow_id = str(uuid.uuid4())
        
        try:
            # Step 1: Log workflow start
            await self._log_workflow_start(workflow_id, "document_processing", db_session)
            
            # Step 2: Process document
            document = await document_processor.process_document(file_content, filename, db_session)
            
            # Step 3: Wait for processing to complete
            await self._wait_for_processing(document.id, db_session)
            
            # Step 4: Get final document content
            content = await document_processor.get_document_content(document.id, db_session)
            
            # Step 5: AI Analysis (if enabled)
            analysis_result = None
            if workflow_config and workflow_config.get("enable_ai_analysis", True):
                analysis_result = await ai_analyzer.analyze_document_content(
                    content, workflow_config.get("analysis_type", "general")
                )
            
            # Step 6: External actions (if configured)
            external_actions = []
            if workflow_config and workflow_config.get("enable_notifications", False):
                # Send Slack notification
                if analysis_result and "summary" in analysis_result:
                    notification_text = f"New document processed: {filename}\n\nSummary: {analysis_result['summary']}"
                else:
                    notification_text = f"New document processed: {filename}"
                
                slack_result = await self.external_actions.send_slack_notification(
                    notification_text, workflow_id, db_session
                )
                external_actions.append(slack_result)
            
            # Step 7: Log workflow completion
            await self._log_workflow_completion(
                workflow_id, "completed", 
                {
                    "document_id": document.id,
                    "analysis_result": analysis_result,
                    "external_actions": external_actions
                },
                db_session
            )
            
            return {
                "workflow_id": workflow_id,
                "status": "completed",
                "document": document,
                "analysis": analysis_result,
                "external_actions": external_actions
            }
            
        except Exception as e:
            # Log workflow failure
            await self._log_workflow_completion(
                workflow_id, "failed", {"error": str(e)}, db_session
            )
            raise
    
    async def execute_search_and_analyze_workflow(
        self,
        query: str,
        search_type: str,
        analysis_type: str,
        db_session: AsyncSession
    ) -> Dict[str, Any]:
        """Execute search and analysis workflow"""
        workflow_id = str(uuid.uuid4())
        
        try:
            # Step 1: Log workflow start
            await self._log_workflow_start(workflow_id, "search_and_analyze", db_session)
            
            # Step 2: Perform search
            from app.api.routes.search import _vector_search, _fulltext_search, _hybrid_search
            
            search_results = []
            if search_type == "vector":
                search_results = await _vector_search(query, 10, 0.7, db_session)
            elif search_type == "fulltext":
                search_results = await _fulltext_search(query, 10, db_session)
            elif search_type == "hybrid":
                search_results = await _hybrid_search(query, 10, 0.7, db_session)
            
            # Step 3: Extract insights from search results
            insights = await ai_analyzer.extract_insights(search_results)
            
            # Step 4: Generate summary if multiple results
            summary = None
            if len(search_results) > 1:
                summary = await ai_analyzer.generate_summary(search_results, "executive")
            
            # Step 5: Send notification with insights
            notification_text = f"Search completed for: '{query}'\n"
            notification_text += f"Found {len(search_results)} documents\n"
            if insights and "key_takeaways" in insights:
                notification_text += f"Key insights: {', '.join(insights['key_takeaways'][:3])}"
            
            slack_result = await self.external_actions.send_slack_notification(
                notification_text, workflow_id, db_session
            )
            
            # Step 6: Log workflow completion
            await self._log_workflow_completion(
                workflow_id, "completed",
                {
                    "query": query,
                    "search_type": search_type,
                    "results_count": len(search_results),
                    "insights": insights,
                    "summary": summary,
                    "external_actions": [slack_result]
                },
                db_session
            )
            
            return {
                "workflow_id": workflow_id,
                "status": "completed",
                "query": query,
                "search_results": search_results,
                "insights": insights,
                "summary": summary,
                "external_actions": [slack_result]
            }
            
        except Exception as e:
            await self._log_workflow_completion(
                workflow_id, "failed", {"error": str(e)}, db_session
            )
            raise
    
    async def execute_batch_analysis_workflow(
        self,
        document_ids: List[str],
        analysis_type: str,
        db_session: AsyncSession
    ) -> Dict[str, Any]:
        """Execute batch analysis workflow"""
        workflow_id = str(uuid.uuid4())
        
        try:
            # Step 1: Log workflow start
            await self._log_workflow_start(workflow_id, "batch_analysis", db_session)
            
            # Step 2: Get document contents
            documents = []
            for doc_id in document_ids:
                content = await document_processor.get_document_content(doc_id, db_session)
                if content:
                    from app.models.document import DocumentSearchResult
                    doc_result = DocumentSearchResult(
                        id=doc_id,
                        filename=f"Document {doc_id[:8]}",
                        content=content,
                        created_at=None
                    )
                    documents.append(doc_result)
            
            # Step 3: Compare documents
            comparison = await ai_analyzer.compare_documents(documents)
            
            # Step 4: Generate summary
            summary = await ai_analyzer.generate_summary(documents, "executive")
            
            # Step 5: Send comprehensive notification
            notification_text = f"Batch analysis completed for {len(documents)} documents\n"
            if summary and "summary" in summary:
                notification_text += f"Summary: {summary['summary']}\n"
            if comparison and "insights" in comparison:
                notification_text += f"Key insights: {', '.join(comparison['insights'][:2])}"
            
            slack_result = await self.external_actions.send_slack_notification(
                notification_text, workflow_id, db_session
            )
            
            # Step 6: Log workflow completion
            await self._log_workflow_completion(
                workflow_id, "completed",
                {
                    "document_ids": document_ids,
                    "analysis_type": analysis_type,
                    "comparison": comparison,
                    "summary": summary,
                    "external_actions": [slack_result]
                },
                db_session
            )
            
            return {
                "workflow_id": workflow_id,
                "status": "completed",
                "document_ids": document_ids,
                "comparison": comparison,
                "summary": summary,
                "external_actions": [slack_result]
            }
            
        except Exception as e:
            await self._log_workflow_completion(
                workflow_id, "failed", {"error": str(e)}, db_session
            )
            raise
    
    async def execute_intelligent_document_routing_workflow(
        self,
        file_content: bytes,
        filename: str,
        db_session: AsyncSession
    ) -> Dict[str, Any]:
        """Execute intelligent document routing workflow"""
        workflow_id = str(uuid.uuid4())
        
        try:
            # Step 1: Log workflow start
            await self._log_workflow_start(workflow_id, "intelligent_routing", db_session)
            
            # Step 2: Process document
            document = await document_processor.process_document(file_content, filename, db_session)
            
            # Step 3: Wait for processing
            await self._wait_for_processing(document.id, db_session)
            
            # Step 4: Get content and analyze
            content = await document_processor.get_document_content(document.id, db_session)
            analysis = await ai_analyzer.analyze_document_content(content, "general")
            
            # Step 5: Determine routing based on analysis
            routing_decision = await self._determine_routing(analysis, content)
            
            # Step 6: Execute routing actions
            routing_actions = []
            
            if routing_decision.get("requires_legal_review"):
                # Send to legal team
                legal_notification = await self.external_actions.send_slack_notification(
                    f"Legal review required for: {filename}\nType: {analysis.get('document_type', 'Unknown')}",
                    workflow_id, db_session,
                    channel="#legal-team"
                )
                routing_actions.append(legal_notification)
            
            if routing_decision.get("requires_financial_review"):
                # Send to finance team
                finance_notification = await self.external_actions.send_slack_notification(
                    f"Financial review required for: {filename}\nAmount: {routing_decision.get('financial_amount', 'N/A')}",
                    workflow_id, db_session,
                    channel="#finance-team"
                )
                routing_actions.append(finance_notification)
            
            if routing_decision.get("create_calendar_event"):
                # Create calendar event
                calendar_event = await self.external_actions.create_calendar_event(
                    f"Document Review: {filename}",
                    f"Review required for {analysis.get('document_type', 'document')}",
                    workflow_id, db_session
                )
                routing_actions.append(calendar_event)
            
            # Step 7: Log workflow completion
            await self._log_workflow_completion(
                workflow_id, "completed",
                {
                    "document_id": document.id,
                    "analysis": analysis,
                    "routing_decision": routing_decision,
                    "routing_actions": routing_actions
                },
                db_session
            )
            
            return {
                "workflow_id": workflow_id,
                "status": "completed",
                "document": document,
                "analysis": analysis,
                "routing_decision": routing_decision,
                "routing_actions": routing_actions
            }
            
        except Exception as e:
            await self._log_workflow_completion(
                workflow_id, "failed", {"error": str(e)}, db_session
            )
            raise
    
    async def _wait_for_processing(self, document_id: str, db_session: AsyncSession, timeout: int = 60):
        """Wait for document processing to complete"""
        start_time = datetime.now()
        while (datetime.now() - start_time).seconds < timeout:
            status = await document_processor.get_document_status(document_id, db_session)
            if status.value in ["completed", "failed"]:
                return status
            await asyncio.sleep(2)
        raise TimeoutError("Document processing timeout")
    
    async def _determine_routing(self, analysis: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Determine document routing based on analysis"""
        routing_decision = {
            "requires_legal_review": False,
            "requires_financial_review": False,
            "create_calendar_event": False,
            "priority": "normal"
        }
        
        # Check for legal documents
        doc_type = analysis.get("document_type", "").lower()
        if any(keyword in doc_type for keyword in ["contract", "agreement", "legal", "policy"]):
            routing_decision["requires_legal_review"] = True
            routing_decision["priority"] = "high"
        
        # Check for financial documents
        if any(keyword in doc_type for keyword in ["invoice", "receipt", "financial", "budget"]):
            routing_decision["requires_financial_review"] = True
        
        # Check for urgent content
        urgent_keywords = ["urgent", "immediate", "asap", "deadline", "critical"]
        if any(keyword in content.lower() for keyword in urgent_keywords):
            routing_decision["priority"] = "urgent"
            routing_decision["create_calendar_event"] = True
        
        return routing_decision
    
    async def _log_workflow_start(self, workflow_id: str, workflow_name: str, db_session: AsyncSession):
        """Log workflow start"""
        query = text("""
            INSERT INTO workflow_executions (id, workflow_name, status, started_at)
            VALUES (:id, :workflow_name, 'running', CURRENT_TIMESTAMP)
        """)
        
        await db_session.execute(query, {
            "id": workflow_id,
            "workflow_name": workflow_name
        })
        await db_session.commit()
    
    async def _log_workflow_completion(
        self, 
        workflow_id: str, 
        status: str, 
        output_data: Dict[str, Any], 
        db_session: AsyncSession
    ):
        """Log workflow completion"""
        query = text("""
            UPDATE workflow_executions 
            SET status = :status, output_data = :output_data, completed_at = CURRENT_TIMESTAMP,
                execution_time_ms = TIMESTAMPDIFF(MICROSECOND, started_at, CURRENT_TIMESTAMP) / 1000
            WHERE id = :workflow_id
        """)
        
        await db_session.execute(query, {
            "workflow_id": workflow_id,
            "status": status,
            "output_data": json.dumps(output_data)
        })
        await db_session.commit()

# Global workflow orchestrator instance
workflow_orchestrator = WorkflowOrchestrator()


