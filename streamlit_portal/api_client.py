import requests
import os
import streamlit as st

class APIClient:
    def __init__(self):
        self.base_url = os.getenv("PLATFORM_API_BASE_URL", "http://platform_api:8000")
        self.api_v1 = f"{self.base_url}/api/v1"

    def _handle_response(self, response):
        try:
            if response.status_code == 204:
                return None
            return response.json()
        except ValueError:
            return response.text

    def get_health(self):
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=5)
            return resp.status_code == 200, self._handle_response(resp)
        except requests.exceptions.RequestException as e:
            return False, str(e)

    # --- KB/RAG ---
    def upload_document(self, file_obj):
        files = {"file": (file_obj.name, file_obj.getvalue(), file_obj.type)}
        resp = requests.post(f"{self.api_v1}/kb/upload", files=files)
        return resp

    def list_documents(self):
        resp = requests.get(f"{self.api_v1}/kb/documents")
        return self._handle_response(resp) if resp.status_code == 200 else []

    # --- Admin ---
    def get_config(self):
        resp = requests.get(f"{self.api_v1}/admin/config")
        return self._handle_response(resp) if resp.status_code == 200 else {}

    def get_users(self):
        resp = requests.get(f"{self.api_v1}/admin/users")
        return self._handle_response(resp) if resp.status_code == 200 else []

    def get_logs(self):
        resp = requests.get(f"{self.api_v1}/admin/logs")
        return self._handle_response(resp) if resp.status_code == 200 else {}

    # --- Test Lab ---
    def create_run(self, run_id, name, persona):
        payload = {"id": run_id, "name": name, "persona": persona}
        resp = requests.post(f"{self.api_v1}/testlab/runs", json=payload)
        return self._handle_response(resp)

    def get_run(self, run_id):
        resp = requests.get(f"{self.api_v1}/testlab/runs/{run_id}")
        return self._handle_response(resp) if resp.status_code == 200 else None

    def send_message(self, run_id, content, role="user"):
        payload = {"content": content, "role": role}
        resp = requests.post(f"{self.api_v1}/testlab/runs/{run_id}/messages", json=payload)
        return self._handle_response(resp)
