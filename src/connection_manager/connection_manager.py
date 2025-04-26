from fastapi import WebSocket
from typing import Dict, List, Optional


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.pairs: Dict[WebSocket, Optional[WebSocket]] = {}
        self.client_id_map: Dict[WebSocket, int] = {}
        self.waiting_for_partner: List[WebSocket] = []

    def get_partner(self, websocket: WebSocket) -> Optional[WebSocket]:
        """Get or assign a chat partner for the given websocket."""
        # If already has a partner, return it
        if websocket in self.pairs and self.pairs[websocket]:
            return self.pairs[websocket]
        
        # If someone is waiting, pair them up
        if self.waiting_for_partner and self.waiting_for_partner[0] != websocket:
            partner = self.waiting_for_partner.pop(0)
            self.pairs[websocket] = partner
            self.pairs[partner] = websocket
            return partner
        
        # If no partner available, add to waiting list
        if websocket not in self.waiting_for_partner:
            self.waiting_for_partner.append(websocket)
        return None

    async def connect(self, websocket: WebSocket, client_id: int):
        """Handle new websocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.pairs[websocket] = None
        self.client_id_map[websocket] = client_id
        print(f"No of active connections: {len(self.active_connections)}")
        print(f"active: {self.active_connections}")
        print(f"pairs: {self.pairs}")
        
        # Send welcome message
        await self.send_personal_message("Connected to chat. Waiting for a partner...", websocket)

    def disconnect(self, websocket: WebSocket):
        """Handle websocket disconnection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Remove from waiting list if present
        if websocket in self.waiting_for_partner:
            self.waiting_for_partner.remove(websocket)
        
        # Clean up partner pairing
        partner = self.pairs.get(websocket)
        if partner:
            self.pairs[partner] = None
        
        # Clean up maps
        self.pairs.pop(websocket, None)
        self.client_id_map.pop(websocket, None)
        print(f"No of active connections: {len(self.active_connections)}")
        print(f"active: {self.active_connections}")
        print(f"pairs: {self.pairs}")

    def get_client_id(self, websocket: WebSocket) -> Optional[int]:
        """Get client ID for the given websocket."""
        return self.client_id_map.get(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific websocket."""
        if websocket in self.active_connections:
            await websocket.send_text(message)

    async def broadcast(self, message: str):
        """Send a message to all connected clients."""
        for connection in self.active_connections:
            await self.send_personal_message(message, connection)
