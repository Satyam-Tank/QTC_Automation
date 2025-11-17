import asyncio
import requests
import base64
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.services import graph_auth

GRAPH_BASE = "https://graph.microsoft.com/v1.0"

logger = logging.getLogger(__name__)

class GraphApiService:
    """A service for interacting with the Microsoft Graph API for mail."""

    def __init__(self, session: requests.Session):
        if not session:
            raise ValueError("An authenticated requests.Session is required.")
        self.session = session

    def get_email_by_id(self, email_id: str) -> Dict[str, Any]:
        url = f"{GRAPH_BASE}/users/{settings.MAILBOX_UPN}/messages/{email_id}"
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_recent_emails(self, limit: int = 10) -> List[Dict[str, Any]]:
        url = f"{GRAPH_BASE}/users/{settings.MAILBOX_UPN}/messages"
        params = {'$top': limit, '$orderby': 'receivedDateTime desc'}
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json().get('value', [])

    def send_email(self, to_email: str, subject: str, body_html: str) -> None:
        url = f"{GRAPH_BASE}/users/{settings.MAILBOX_UPN}/sendMail"
        message = { "message": { "subject": subject, "body": { "contentType": "HTML", "content": body_html }, "toRecipients": [{ "emailAddress": { "address": to_email } }] } }
        response = self.session.post(url, json=message, timeout=30)
        response.raise_for_status()
        print(f"Email sent successfully to {to_email}")

    def create_subscription(self) -> Dict[str, Any]:
        expiration_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        body = {
            "changeType": "created",
            "notificationUrl": settings.WEBHOOK_NOTIFICATION_URL,
            "resource": f"/users/{settings.MAILBOX_UPN}/messages",
            "expirationDateTime": expiration_time,
            "clientState": settings.CLIENT_STATE_SECRET
        }
        url = f"{GRAPH_BASE}/subscriptions"
        response = self.session.post(url, json=body, timeout=30)
        if response.status_code != 201:
            raise Exception(f"Failed to create subscription: {response.text}")
        return response.json()

    def list_subscriptions(self) -> List[Dict[str, Any]]:
        url = f"{GRAPH_BASE}/subscriptions"
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.json().get('value', [])

    def delete_subscription(self, sub_id: str) -> None:
        url = f"{GRAPH_BASE}/subscriptions/{sub_id}"
        response = self.session.delete(url, timeout=30)
        if response.status_code != 204:
            raise Exception(f"Failed to delete subscription: {response.text}")
        print(f"Subscription {sub_id} deleted.")

    def get_attachments(self, email_id: str) -> List[Dict[str, Any]]:
        url = f"{GRAPH_BASE}/users/{settings.MAILBOX_UPN}/messages/{email_id}/attachments"
        response = self.session.get(url, timeout=60)
        response.raise_for_status()
        attachments_data = response.json().get('value', [])
        processed_attachments = []
        for att in attachments_data:
            if att.get('@odata.type') == '#microsoft.graph.fileAttachment' and att.get('contentBytes'):
                processed_attachments.append({
                    "name": att.get('name'),
                    "content_type": att.get('contentType'),
                    "content_bytes": base64.b64decode(att.get('contentBytes'))
                })
        return processed_attachments

# --- NEW HELPER FUNCTIONS ---

async def _get_access_token_async() -> str:
    """Async helper to get a token."""
    # DEBUG LOGGING
    logger.info("=" * 60)
    logger.info("DEBUG: Checking for HARDCODED_ACCESS_TOKEN")
    logger.info(f"DEBUG: Token exists: {bool(settings.HARDCODED_ACCESS_TOKEN)}")
    logger.info(f"DEBUG: Token is None: {settings.HARDCODED_ACCESS_TOKEN is None}")
    logger.info(f"DEBUG: Token is empty string: {settings.HARDCODED_ACCESS_TOKEN == ''}")
    if settings.HARDCODED_ACCESS_TOKEN:
        logger.info(f"DEBUG: Token length: {len(settings.HARDCODED_ACCESS_TOKEN)}")
        logger.info(f"DEBUG: Token starts with: {settings.HARDCODED_ACCESS_TOKEN[:20]}...")
    logger.info("=" * 60)
    
    if settings.HARDCODED_ACCESS_TOKEN:
        logger.info("✅ Using HARDCODED access token from environment.")
        return settings.HARDCODED_ACCESS_TOKEN
    
    logger.info("⚠️  No hardcoded token. Running semi-auto auth flow...")
    scopes = ['User.Read', 'Mail.Read', 'Mail.Send', 'Mail.ReadWrite']
    access_token = await graph_auth.get_delegated_access_token(scopes=scopes)
    logger.info("Authentication successful.")
    return access_token

def get_graph_service_sync() -> GraphApiService:
    """
    SYNC helper for our background job. Uses asyncio.run().
    """
    logger.info("Authenticating to Microsoft Graph (SYNC)...")
    # This is safe because processing.py is NOT in an event loop
    access_token = asyncio.run(_get_access_token_async())
    session = graph_auth.get_graph_client(access_token)
    return GraphApiService(session)

async def get_graph_service_async() -> GraphApiService:
    """
    ASYNC helper for our manage_subscription.py script. Uses await.
    """
    logger.info("Authenticating to Microsoft Graph (ASYNC)...")
    # This is safe because manage_subscription.py IS in an event loop
    access_token = await _get_access_token_async()
    session = graph_auth.get_graph_client(access_token)
    return GraphApiService(session)