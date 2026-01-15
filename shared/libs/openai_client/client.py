import httpx
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("OpenAIClient")

class OpenAIClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set for OpenAIClient")
        
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "assistants=v2" # Required for Vector Stores
        }

    async def create_vector_store(self, name: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/vector_stores",
                headers=self.headers,
                json={"name": name}
            )
            resp.raise_for_status()
            return resp.json()

    async def upload_file(self, file_content: bytes, filename: str, purpose: str = "assistants") -> Dict[str, Any]:
        files = {"file": (filename, file_content)}
        data = {"purpose": purpose}
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/files",
                headers=self.headers,
                files=files,
                data=data
            )
            resp.raise_for_status()
            return resp.json()

    async def create_vector_store_file(self, vector_store_id: str, file_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/vector_stores/{vector_store_id}/files",
                headers=self.headers,
                json={"file_id": file_id}
            )
            resp.raise_for_status()
            return resp.json()

    async def delete_vector_store_file(self, vector_store_id: str, file_id: str) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{self.base_url}/vector_stores/{vector_store_id}/files/{file_id}",
                headers=self.headers
            )
            return resp.status_code == 200

    async def get_vector_store_file(self, vector_store_id: str, file_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/vector_stores/{vector_store_id}/files/{file_id}",
                headers=self.headers
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()
