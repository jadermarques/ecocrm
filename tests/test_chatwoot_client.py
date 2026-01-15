import pytest
import respx
from httpx import Response
from shared.libs.chatwoot_client import ChatwootClient

@pytest.mark.asyncio
async def test_create_message_success():
    base_url = "https://test.chatwoot.com"
    token = "test_token"
    account_id = 1
    conversation_id = 100
    
    client = ChatwootClient(base_url, token, account_id)
    
    async with respx.mock(base_url=base_url) as respx_mock:
        route = respx_mock.post(
            f"/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages"
        ).mock(return_value=Response(200, json={"id": 1, "content": "hello"}))
        
        result = await client.create_message(conversation_id, "hello")
        
        assert result["content"] == "hello"
        assert route.called
        
        # Verify Headers
        assert route.calls.last.request.headers["api_access_token"] == token
        # Verify Payload
        payload = pd = route.calls.last.request.read()
        assert b"hello" in payload
