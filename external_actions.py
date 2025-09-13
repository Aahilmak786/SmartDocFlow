import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json

from app.core.config import settings

class ExternalActionService:
    def __init__(self):
        self.slack_client = None
        self.calendar_service = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize external API clients"""
        try:
            # Initialize Slack client
            if settings.SLACK_BOT_TOKEN:
                from slack_sdk.web import WebClient
                self.slack_client = WebClient(token=settings.SLACK_BOT_TOKEN)
        except Exception as e:
            print(f"Failed to initialize Slack client: {e}")
        
        try:
            # Initialize Google Calendar client
            if settings.GOOGLE_CALENDAR_CREDENTIALS:
                from google.oauth2.credentials import Credentials
                from googleapiclient.discovery import build
                
                # This would need proper OAuth2 setup in a real implementation
                # For now, we'll create a mock service
                self.calendar_service = None  # Would be actual calendar service
        except Exception as e:
            print(f"Failed to initialize Google Calendar client: {e}")
    
    async def send_slack_notification(
        self, 
        message: str, 
        workflow_id: str, 
        db_session: AsyncSession,
        channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send Slack notification"""
        action_id = str(uuid.uuid4())
        
        try:
            # Use default channel if not specified
            target_channel = channel or settings.SLACK_CHANNEL_ID or "#general"
            
            # Send message via Slack API
            if self.slack_client:
                response = self.slack_client.chat_postMessage(
                    channel=target_channel,
                    text=message,
                    blocks=[
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": message
                            }
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"Workflow ID: {workflow_id}"
                                }
                            ]
                        }
                    ]
                )
                
                # Log successful action
                await self._log_external_action(
                    action_id, workflow_id, "slack_notification", 
                    {"channel": target_channel, "message": message},
                    {"success": True, "response": response},
                    db_session
                )
                
                return {
                    "action_id": action_id,
                    "type": "slack_notification",
                    "status": "sent",
                    "channel": target_channel,
                    "message": message
                }
            else:
                # Mock response for development
                print(f"[SLACK] {target_channel}: {message}")
                
                await self._log_external_action(
                    action_id, workflow_id, "slack_notification",
                    {"channel": target_channel, "message": message},
                    {"success": True, "mock": True},
                    db_session
                )
                
                return {
                    "action_id": action_id,
                    "type": "slack_notification",
                    "status": "sent",
                    "channel": target_channel,
                    "message": message,
                    "mock": True
                }
                
        except Exception as e:
            # Log failed action
            await self._log_external_action(
                action_id, workflow_id, "slack_notification",
                {"channel": target_channel, "message": message},
                {"success": False, "error": str(e)},
                db_session
            )
            
            return {
                "action_id": action_id,
                "type": "slack_notification",
                "status": "failed",
                "error": str(e)
            }
    
    async def create_calendar_event(
        self, 
        title: str, 
        description: str, 
        workflow_id: str, 
        db_session: AsyncSession,
        start_time: Optional[datetime] = None,
        duration_minutes: int = 60
    ) -> Dict[str, Any]:
        """Create Google Calendar event"""
        action_id = str(uuid.uuid4())
        
        try:
            # Set default start time to 1 hour from now
            if not start_time:
                start_time = datetime.now() + timedelta(hours=1)
            
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            # Create calendar event via Google Calendar API
            if self.calendar_service:
                event = {
                    'summary': title,
                    'description': description,
                    'start': {
                        'dateTime': start_time.isoformat(),
                        'timeZone': 'UTC',
                    },
                    'end': {
                        'dateTime': end_time.isoformat(),
                        'timeZone': 'UTC',
                    },
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'email', 'minutes': 24 * 60},
                            {'method': 'popup', 'minutes': 30},
                        ],
                    },
                }
                
                # This would be the actual API call
                # created_event = self.calendar_service.events().insert(
                #     calendarId='primary', body=event
                # ).execute()
                
                # For now, we'll mock the response
                created_event = {"id": f"mock_event_{action_id}", "htmlLink": "#"}
                
                # Log successful action
                await self._log_external_action(
                    action_id, workflow_id, "calendar_event",
                    {"title": title, "description": description, "start_time": start_time.isoformat()},
                    {"success": True, "event_id": created_event["id"]},
                    db_session
                )
                
                return {
                    "action_id": action_id,
                    "type": "calendar_event",
                    "status": "created",
                    "event_id": created_event["id"],
                    "title": title,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                }
            else:
                # Mock response for development
                print(f"[CALENDAR] Event created: {title} at {start_time}")
                
                await self._log_external_action(
                    action_id, workflow_id, "calendar_event",
                    {"title": title, "description": description, "start_time": start_time.isoformat()},
                    {"success": True, "mock": True},
                    db_session
                )
                
                return {
                    "action_id": action_id,
                    "type": "calendar_event",
                    "status": "created",
                    "title": title,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "mock": True
                }
                
        except Exception as e:
            # Log failed action
            await self._log_external_action(
                action_id, workflow_id, "calendar_event",
                {"title": title, "description": description},
                {"success": False, "error": str(e)},
                db_session
            )
            
            return {
                "action_id": action_id,
                "type": "calendar_event",
                "status": "failed",
                "error": str(e)
            }
    
    async def send_email_notification(
        self, 
        to_email: str, 
        subject: str, 
        body: str, 
        workflow_id: str, 
        db_session: AsyncSession
    ) -> Dict[str, Any]:
        """Send email notification"""
        action_id = str(uuid.uuid4())
        
        try:
            # This would integrate with an email service like SendGrid, AWS SES, etc.
            # For now, we'll mock the email sending
            
            print(f"[EMAIL] To: {to_email}, Subject: {subject}")
            print(f"[EMAIL] Body: {body}")
            
            # Log successful action
            await self._log_external_action(
                action_id, workflow_id, "email",
                {"to_email": to_email, "subject": subject, "body": body},
                {"success": True, "mock": True},
                db_session
            )
            
            return {
                "action_id": action_id,
                "type": "email",
                "status": "sent",
                "to_email": to_email,
                "subject": subject,
                "mock": True
            }
            
        except Exception as e:
            # Log failed action
            await self._log_external_action(
                action_id, workflow_id, "email",
                {"to_email": to_email, "subject": subject, "body": body},
                {"success": False, "error": str(e)},
                db_session
            )
            
            return {
                "action_id": action_id,
                "type": "email",
                "status": "failed",
                "error": str(e)
            }
    
    async def trigger_webhook(
        self, 
        webhook_url: str, 
        payload: Dict[str, Any], 
        workflow_id: str, 
        db_session: AsyncSession
    ) -> Dict[str, Any]:
        """Trigger webhook"""
        action_id = str(uuid.uuid4())
        
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )
                
                response.raise_for_status()
                
                # Log successful action
                await self._log_external_action(
                    action_id, workflow_id, "webhook",
                    {"webhook_url": webhook_url, "payload": payload},
                    {"success": True, "status_code": response.status_code},
                    db_session
                )
                
                return {
                    "action_id": action_id,
                    "type": "webhook",
                    "status": "triggered",
                    "webhook_url": webhook_url,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            # Log failed action
            await self._log_external_action(
                action_id, workflow_id, "webhook",
                {"webhook_url": webhook_url, "payload": payload},
                {"success": False, "error": str(e)},
                db_session
            )
            
            return {
                "action_id": action_id,
                "type": "webhook",
                "status": "failed",
                "error": str(e)
            }
    
    async def _log_external_action(
        self,
        action_id: str,
        workflow_id: str,
        action_type: str,
        action_data: Dict[str, Any],
        response_data: Dict[str, Any],
        db_session: AsyncSession
    ):
        """Log external action to database"""
        try:
            query = text("""
                INSERT INTO external_actions (id, workflow_execution_id, action_type, action_data, status, response_data)
                VALUES (:id, :workflow_execution_id, :action_type, :action_data, :status, :response_data)
            """)
            
            status = "sent" if response_data.get("success", False) else "failed"
            
            await db_session.execute(query, {
                "id": action_id,
                "workflow_execution_id": workflow_id,
                "action_type": action_type,
                "action_data": json.dumps(action_data),
                "status": status,
                "response_data": json.dumps(response_data)
            })
            
            await db_session.commit()
            
        except Exception as e:
            print(f"Failed to log external action: {e}")
            # Don't raise exception for logging failures
    
    async def get_action_status(self, action_id: str, db_session: AsyncSession) -> Optional[Dict[str, Any]]:
        """Get status of an external action"""
        try:
            query = text("""
                SELECT action_type, action_data, status, response_data, created_at, executed_at
                FROM external_actions
                WHERE id = :action_id
            """)
            
            result = await db_session.execute(query, {"action_id": action_id})
            row = result.fetchone()
            
            if row:
                return {
                    "action_id": action_id,
                    "action_type": row[0],
                    "action_data": json.loads(row[1]) if row[1] else {},
                    "status": row[2],
                    "response_data": json.loads(row[3]) if row[3] else {},
                    "created_at": row[4],
                    "executed_at": row[5]
                }
            
            return None
            
        except Exception as e:
            print(f"Failed to get action status: {e}")
            return None


