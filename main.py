from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from src.connection_manager import ConnectionManager
manager = ConnectionManager()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend"), name="static")
templates = Jinja2Templates(directory="frontend/templates")


@app.get("/")
async def get():
    return templates.TemplateResponse("index.html", {"request": {}})


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