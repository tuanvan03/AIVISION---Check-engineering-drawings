import json
from typing import Dict
from fastapi import WebSocket

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, task_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[task_id] = websocket
        await websocket.send_text(json.dumps({"event": "connected", "data": {"task_id": task_id}}))

    def disconnect(self, task_id: str):
        if task_id in self.active_connections:
            del self.active_connections[task_id]

    async def send_personal_message(self, message: str, task_id: str):
        if task_id in self.active_connections:
            websocket = self.active_connections[task_id]
            try:
                await websocket.send_text(message)
            except Exception:
                self.disconnect(task_id)

    async def send_progress(self, task_id: str, step: str, message: str):
        payload = json.dumps({"event": "progress", "data": {"step": step, "message": message}})
        await self.send_personal_message(payload, task_id)

    async def send_result(self, task_id: str, result: dict):
        payload = json.dumps({"event": "result", "data": result})
        if task_id in self.active_connections:
            websocket = self.active_connections[task_id]
            try:
                await websocket.send_text(payload)
                await websocket.close()
            except Exception:
                pass
            finally:
                self.disconnect(task_id)

    async def send_error(self, task_id: str, code: str, message: str):
        payload = json.dumps({"event": "error", "data": {"code": code, "message": message}})
        if task_id in self.active_connections:
            websocket = self.active_connections[task_id]
            try:
                await websocket.send_text(payload)
                await websocket.close(code=4000)
            except Exception:
                pass
            finally:
                self.disconnect(task_id)

websocket_manager = WebSocketManager()
