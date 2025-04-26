from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn


app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://localhost:8000/ws/${client_id}`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


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


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            partner = manager.get_partner(websocket)
            if partner:
                await manager.send_personal_message(f"YOU: {data}", websocket)
                await manager.send_personal_message(f"{manager.get_client_id(websocket)}: {data}", partner)
            else:
                await manager.send_personal_message(f"Could not find partner for you", websocket)
    except WebSocketDisconnect:
        await manager.send_personal_message(f"Client #{manager.get_client_id(websocket)} left the chat", manager.get_partner(websocket))
        manager.disconnect(websocket)
        

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)