import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.pairs: dict[WebSocket, WebSocket] = {}
        self.pairs_count = 0
        self.client_id_map = {}

    def get_partner(self, websocket: WebSocket):
        if self.pairs.get(websocket, None):
            return self.pairs[websocket]
        else:
            for connection in self.active_connections:
                if connection not in self.pairs.values():
                    self.pairs[websocket] = connection
                    self.pairs[connection] = websocket
                    return connection
        return None

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"active connections: {self.active_connections}")
        
        self.pairs[websocket] = None
        self.client_id_map[websocket] = client_id

    def get_client_id(self, websocket: WebSocket):
        return self.client_id_map.get(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()
