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

    # --- Bot Studio ---
    # Agents
    def list_agents(self):
        resp = requests.get(f"{self.api_v1}/botstudio/agents")
        return self._handle_response(resp) if resp.status_code == 200 else []

    def create_agent(self, data):
        resp = requests.post(f"{self.api_v1}/botstudio/agents", json=data)
        return self._handle_response(resp)

    def delete_agent(self, agent_id):
        resp = requests.delete(f"{self.api_v1}/botstudio/agents/{agent_id}")
        return resp.status_code == 200

    # Tasks
    # --- AI Management ---
    def list_ai_providers(self):
        resp = requests.get(f"{self.api_v1}/ai/providers")
        return self._handle_response(resp) if resp.status_code == 200 else []

    def create_ai_provider(self, data):
        resp = requests.post(f"{self.api_v1}/ai/providers", json=data)
        return self._handle_response(resp)

    def update_ai_provider(self, provider_id, data):
        resp = requests.put(f"{self.api_v1}/ai/providers/{provider_id}", json=data)
        return self._handle_response(resp)

    # --- KB/RAG ---
    def list_kbs(self):
        resp = requests.get(f"{self.api_v1}/kb")
        return self._handle_response(resp) if resp.status_code == 200 else []

    def create_kb(self, name, description):
        resp = requests.post(f"{self.api_v1}/kb", json={"name": name, "description": description})
        return self._handle_response(resp)

    def get_kb(self, kb_id):
        resp = requests.get(f"{self.api_v1}/kb/{kb_id}")
        return self._handle_response(resp) if resp.status_code == 200 else None

    # Replaces old upload_document logic which was generic
    def upload_kb_file(self, kb_id, file_obj):
        # file_obj is Streamlit UploadedFile
        files = {"file": (file_obj.name, file_obj.getvalue(), file_obj.type)}
        resp = requests.post(f"{self.api_v1}/kb/{kb_id}/files", files=files)
        return self._handle_response(resp)

    def delete_kb_file(self, kb_id, file_id):
        resp = requests.delete(f"{self.api_v1}/kb/{kb_id}/files/{file_id}")
        return resp.status_code == 200

    def query_kb(self, kb_id, query):
        resp = requests.post(f"{self.api_v1}/kb/{kb_id}/query", json={"query": query})
        return self._handle_response(resp) if resp.status_code == 200 else {}

    # --- BI / Data Hub ---
    def get_bi_volume(self, date_from, date_to, inbox_id=None):
        params = {"date_from": date_from, "date_to": date_to}
        if inbox_id: params["inbox_id"] = inbox_id
        resp = requests.get(f"{self.api_v1}/bi/volume", params=params)
        return self._handle_response(resp) if resp.status_code == 200 else []

    def get_bi_agent_volume(self, date_from, date_to):
        params = {"date_from": date_from, "date_to": date_to}
        resp = requests.get(f"{self.api_v1}/bi/agent-volume", params=params)
        return self._handle_response(resp) if resp.status_code == 200 else []

    def get_bi_time_metrics(self, date_from, date_to, inbox_id=None):
        params = {"date_from": date_from, "date_to": date_to}
        if inbox_id: params["inbox_id"] = inbox_id
        resp = requests.get(f"{self.api_v1}/bi/time-metrics", params=params)
        return self._handle_response(resp) if resp.status_code == 200 else {}

    def get_bi_backlog(self, inbox_id=None):
        params = {}
        if inbox_id: params["inbox_id"] = inbox_id
        resp = requests.get(f"{self.api_v1}/bi/backlog", params=params)
        return self._handle_response(resp) if resp.status_code == 200 else []

    def delete_ai_provider(self, provider_id):
        resp = requests.delete(f"{self.api_v1}/ai/providers/{provider_id}")
        return resp.status_code == 200

    def list_ai_models(self):
        resp = requests.get(f"{self.api_v1}/ai/models")
        return self._handle_response(resp) if resp.status_code == 200 else []

    def list_enabled_ai_models(self):
        resp = requests.get(f"{self.api_v1}/ai/models/enabled")
        return self._handle_response(resp) if resp.status_code == 200 else []

    def create_ai_model(self, data):
        resp = requests.post(f"{self.api_v1}/ai/models", json=data)
        return self._handle_response(resp)

    def update_ai_model(self, model_id, data):
        resp = requests.put(f"{self.api_v1}/ai/models/{model_id}", json=data)
        return self._handle_response(resp)

    def delete_ai_model(self, model_id):
        resp = requests.delete(f"{self.api_v1}/ai/models/{model_id}")
        return resp.status_code == 200

    def list_tasks(self):
        resp = requests.get(f"{self.api_v1}/botstudio/tasks")
        return self._handle_response(resp) if resp.status_code == 200 else []

    def create_task(self, data):
        resp = requests.post(f"{self.api_v1}/botstudio/tasks", json=data)
        return self._handle_response(resp)

    def delete_task(self, task_id):
        resp = requests.delete(f"{self.api_v1}/botstudio/tasks/{task_id}")
        return resp.status_code == 200

    # Crews
    def list_crews(self):
        resp = requests.get(f"{self.api_v1}/botstudio/crews")
        # Ensure we return a list, even if empty or error handled
        res = self._handle_response(resp)
        return res if isinstance(res, list) else []

    def get_crew(self, crew_id):
        resp = requests.get(f"{self.api_v1}/botstudio/crews/{crew_id}")
        return self._handle_response(resp) if resp.status_code == 200 else None

    def create_crew(self, data):
        resp = requests.post(f"{self.api_v1}/botstudio/crews", json=data)
        return self._handle_response(resp)

    def send_message(self, run_id, content, role="user", crew_version_id=None):
        payload = {"content": content, "role": role}
        if crew_version_id:
            payload["crew_version_id"] = crew_version_id
        resp = requests.post(f"{self.api_v1}/testlab/runs/{run_id}/messages", json=payload)
        return self._handle_response(resp)

    def link_tasks_to_crew(self, crew_id, links):
        # links = [{"task_id": 1, "step_order": 1}, ...]
        resp = requests.post(f"{self.api_v1}/botstudio/crews/{crew_id}/tasks", json=links)
        return self._handle_response(resp)

    def publish_crew(self, crew_id, version_tag, model_id=None):
        url = f"{self.api_v1}/botstudio/crews/{crew_id}/publish?version_tag={version_tag}"
        if model_id:
            url += f"&model_id={model_id}"
        resp = requests.post(url)
        return self._handle_response(resp)
