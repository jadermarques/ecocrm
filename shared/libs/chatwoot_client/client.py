import httpx
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class ChatwootClient:
    def __init__(self, base_url: str, api_access_token: str, account_id: int):
        self.base_url = base_url.rstrip('/')
        self.api_access_token = api_access_token
        self.account_id = account_id

    async def create_message(
        self, 
        conversation_id: int, 
        content: str, 
        private: bool = False, 
        message_type: str = "outgoing"
    ) -> Optional[Dict[str, Any]]:
        """
        Creates a new message in a conversation.
        Ref: https://www.chatwoot.com/docs/product/others/api/contacts#create-a-new-contact
        (Actually: https://www.chatwoot.com/developers/api/#tag/Messages/operation/create-a-new-message)
        """
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/messages"
        
        headers = {
            "api_access_token": self.api_access_token,
            "Content-Type": "application/json"
        }
        
        payload = {
            "content": content,
            "message_type": message_type,
            "private": private,
            "content_type": "text"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Chatwoot API Error ({e.response.status_code}): {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Failed to send message to Chatwoot: {str(e)}")
            raise
    async def _get_request(self, url: str, params: Dict[str, Any] = None) -> Any:
        headers = {"api_access_token": self.api_access_token}
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            return resp.json()

    async def list_conversations(self, page: int = 1, status: str = "all", inbox_id: int = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations"
        params = {"page": page, "status": status}
        if inbox_id:
            params["inbox_id"] = inbox_id
        return await self._get_request(url, params)

    async def get_conversation_details(self, conversation_id: int) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations/{conversation_id}"
        return await self._get_request(url)

    async def get_messages(self, conversation_id: int) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/messages"
        return await self._get_request(url)
    
    async def get_conversation_reporting_events(self, conversation_id: int) -> Any:
        # Note: Reporting events endpoint might differ based on version, assuming standard/documented path
        # If not standard, we might need another approach, but using the requested path:
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/reporting_events"
        return await self._get_request(url)

    async def get_account_reporting_events(
        self, 
        page: int = 1, 
        since: int = None, 
        until: int = None, 
        type: str = None
    ) -> Any:
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/reporting_events"
        params = {"page": page}
        if since: params["since"] = since
        if until: params["until"] = until
        if type: params["type"] = type
        return await self._get_request(url, params)
