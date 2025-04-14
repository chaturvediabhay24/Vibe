import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request

from src.connection_manager import ConnectionManager

app = FastAPI()


manager = ConnectionManager()


# Mount static files directory
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Set up templates
templates = Jinja2Templates(directory="frontend/templates")


# Routes
@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            partner = manager.get_partner(websocket)
            if partner:
                await manager.send_personal_message(f"Client #{client_id} says: {data}", partner)
            else:
                await manager.send_personal_message("No partner available", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")

if __name__ == "__main__":
    import uvicorn
    # logger.info("Starting chat server with matching...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
