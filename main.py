from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from src.connection_manager import ConnectionManager
import json
from datetime import datetime

manager = ConnectionManager()

app = FastAPI(title="Vibe Chat")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from frontend directory
app.mount("/static", StaticFiles(directory="frontend"), name="static")
templates = Jinja2Templates(directory="frontend/templates")


@app.get("/")
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            partner = manager.get_partner(websocket)
            if partner:
                # Send message to sender
                # await manager.send_personal_message(data, websocket)
                # Send message to partner
                await manager.send_personal_message(data, partner)
            else:
                await manager.send_personal_message("Waiting for someone to chat with...", websocket)
    except WebSocketDisconnect:
        partner = manager.get_partner(websocket)
        if partner:
            await manager.send_personal_message("Your chat partner has disconnected.", partner)
        manager.disconnect(websocket)
        

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
