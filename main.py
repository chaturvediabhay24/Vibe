from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request, Form
import json
import uuid
import asyncio
from typing import List, Dict, Optional, Set
import logging
from datetime import datetime
import random

# Import the matcher from the matching package
from matching import matcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Vibe - Online Chat Matching")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

# User profiles storage
user_profiles = {}

# Connected WebSocket clients
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_count = 0
        # Dictionary to store chat history for each pair: {(user1_id, user2_id): [messages]}
        self.chat_history: Dict[tuple, List[Dict]] = {}
        # Dictionary to store typing status: {user_id: bool}
        self.typing_status: Dict[str, bool] = {}
        # Dictionary to store online users
        self.online_users: Set[str] = set()
        # Dictionary to store user preferences: {user_id: {preference_key: value}}
        self.user_preferences: Dict[str, Dict] = {}
        # Dictionary to store saved contacts: {user_id: [contact_ids]}
        self.saved_contacts: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_count += 1
        self.online_users.add(client_id)
        logger.info(f"Client {client_id} connected. Total clients: {self.client_count}")
        
        # Initialize user data if not exists
        if client_id not in self.user_preferences:
            self.user_preferences[client_id] = {}
        
        if client_id not in self.saved_contacts:
            self.saved_contacts[client_id] = []
        
        # Broadcast online status to saved contacts
        await self.broadcast_status_to_contacts(client_id, "online")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            self.client_count -= 1
            if client_id in self.online_users:
                self.online_users.remove(client_id)
            if client_id in self.typing_status:
                del self.typing_status[client_id]
            logger.info(f"Client {client_id} disconnected. Total clients: {self.client_count}")
            
            # Broadcast offline status to saved contacts
            asyncio.create_task(self.broadcast_status_to_contacts(client_id, "offline"))

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

    async def broadcast_status_to_contacts(self, user_id: str, status: str):
        """Broadcast status updates to all saved contacts"""
        if user_id in self.saved_contacts:
            for contact_id in self.saved_contacts[user_id]:
                if contact_id in self.active_connections:
                    status_message = {
                        "type": "contact_status",
                        "contact_id": user_id,
                        "status": status,
                        "timestamp": datetime.now().isoformat()
                    }
                    await self.send_personal_message(json.dumps(status_message), contact_id)

    def set_typing_status(self, user_id: str, is_typing: bool):
        """Set the typing status for a user"""
        self.typing_status[user_id] = is_typing

    async def broadcast_typing_status(self, user_id: str, partner_id: str):
        """Broadcast typing status to the chat partner"""
        if partner_id in self.active_connections:
            is_typing = self.typing_status.get(user_id, False)
            typing_message = {
                "type": "typing_status",
                "user_id": user_id,
                "is_typing": is_typing
            }
            await self.send_personal_message(json.dumps(typing_message), partner_id)

    def get_chat_history(self, user1_id: str, user2_id: str) -> List[Dict]:
        """Get chat history for a pair of users"""
        # Sort user IDs to ensure consistent key regardless of order
        pair = tuple(sorted([user1_id, user2_id]))
        return self.chat_history.get(pair, [])

    def add_to_chat_history(self, user1_id: str, user2_id: str, message: Dict):
        """Add a message to the chat history for a pair of users"""
        # Sort user IDs to ensure consistent key regardless of order
        pair = tuple(sorted([user1_id, user2_id]))
        if pair not in self.chat_history:
            self.chat_history[pair] = []
        
        # Add message to history (limit to last 100 messages)
        self.chat_history[pair].append(message)
        if len(self.chat_history[pair]) > 100:
            self.chat_history[pair].pop(0)
    
    def save_contact(self, user_id: str, contact_id: str) -> bool:
        """Save a contact to a user's contact list"""
        if user_id not in self.saved_contacts:
            self.saved_contacts[user_id] = []
        
        if contact_id not in self.saved_contacts[user_id]:
            self.saved_contacts[user_id].append(contact_id)
            return True
        return False
    
    def get_saved_contacts(self, user_id: str) -> List[str]:
        """Get a user's saved contacts"""
        return self.saved_contacts.get(user_id, [])
    
    def is_user_online(self, user_id: str) -> bool:
        """Check if a user is online"""
        return user_id in self.online_users
    
    def set_user_preference(self, user_id: str, key: str, value):
        """Set a user preference"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}
        
        self.user_preferences[user_id][key] = value
    
    def get_user_preference(self, user_id: str, key: str, default=None):
        """Get a user preference"""
        if user_id not in self.user_preferences:
            return default
        
        return self.user_preferences[user_id].get(key, default)


manager = ConnectionManager()

# Routes
@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/stats")
async def get_stats():
    """Get application statistics"""
    return {
        "online_users": len(manager.online_users),
        "active_chats": matcher.get_active_pairs_count(),
        "waiting_users": matcher.get_waiting_count()
    }

@app.post("/api/profile")
async def update_profile(user_id: str = Form(...), display_name: Optional[str] = Form(None), 
                        interests: Optional[str] = Form(None), age: Optional[int] = Form(None)):
    """Update a user's profile"""
    if user_id not in user_profiles:
        user_profiles[user_id] = {}
    
    if display_name:
        user_profiles[user_id]["display_name"] = display_name
    
    if interests:
        user_profiles[user_id]["interests"] = interests.split(",")
    
    if age:
        user_profiles[user_id]["age"] = age
    
    return user_profiles[user_id]

@app.get("/api/profile/{user_id}")
async def get_profile(user_id: str):
    """Get a user's profile"""
    if user_id not in user_profiles:
        return {"error": "Profile not found"}
    
    return user_profiles[user_id]

@app.post("/api/contacts/save")
async def save_contact(user_id: str = Form(...), contact_id: str = Form(...)):
    """Save a contact to a user's contact list"""
    success = manager.save_contact(user_id, contact_id)
    if success:
        return {"status": "success", "message": "Contact saved"}
    else:
        return {"status": "info", "message": "Contact already saved"}

@app.get("/api/contacts/{user_id}")
async def get_contacts(user_id: str):
    """Get a user's saved contacts"""
    contacts = manager.get_saved_contacts(user_id)
    contact_data = []
    
    for contact_id in contacts:
        contact_info = {
            "id": contact_id,
            "online": manager.is_user_online(contact_id),
            "profile": user_profiles.get(contact_id, {})
        }
        contact_data.append(contact_info)
    
    return contact_data

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    partner_id = None
    match_task = None
    
    try:
        # Send initial status message
        status_message = {
            "type": "status",
            "status": "waiting",
            "message": "Waiting for someone to join the chat...",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(status_message))
        
        # Start looking for a match in the background
        match_task = asyncio.create_task(matcher.find_match(client_id))
        
        # Process incoming messages while waiting for a match
        while True:
            # Use wait_for to allow processing messages while waiting for match
            # Create a task for receiving messages
            receive_task = asyncio.create_task(websocket.receive_text())
            
            # Wait for either the match task or the receive task to complete
            done, pending = await asyncio.wait(
                [receive_task, match_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel the receive task if it's still pending
            if receive_task in pending:
                receive_task.cancel()
            
            for task in done:
                if task is match_task:
                    # We found a match!
                    partner_id = task.result()
                    
                    # Send match notification
                    match_message = {
                        "type": "status",
                        "status": "matched",
                        "message": f"You are now chatting with User {partner_id}",
                        "partnerId": partner_id,
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send_text(json.dumps(match_message))
                    
                    # Send chat history if any
                    history = manager.get_chat_history(client_id, partner_id)
                    for msg in history:
                        await websocket.send_text(json.dumps(msg))
                    
                    # Create a new match task that just waits forever
                    # (we're already matched, so we don't need to find another match)
                    match_task = asyncio.create_task(asyncio.sleep(float('inf')))
                else:
                    # We received a message
                    data = task.result()
                    try:
                        message_data = json.loads(data)
                        
                        # Handle different message types
                        if message_data.get("type") == "command":
                            # Handle commands
                            command = message_data.get("command", "").lower()
                            
                            if command == "skip":
                                # Skip current match and find a new one
                                if partner_id:
                                    # Notify the partner that this user has skipped
                                    skip_message = {
                                        "type": "status",
                                        "status": "skipped",
                                        "message": "Your chat partner has skipped this conversation.",
                                        "timestamp": datetime.now().isoformat()
                                    }
                                    await manager.send_personal_message(json.dumps(skip_message), partner_id)
                                    
                                    # End the chat in the matcher
                                    matcher.end_chat(client_id)
                                    
                                    # Reset partner_id
                                    partner_id = None
                                    
                                    # Send waiting message to this user
                                    waiting_message = {
                                        "type": "status",
                                        "status": "waiting",
                                        "message": "Looking for a new match...",
                                        "timestamp": datetime.now().isoformat()
                                    }
                                    await websocket.send_text(json.dumps(waiting_message))
                                    
                                    # Start looking for a new match
                                    match_task = asyncio.create_task(matcher.find_match(client_id))
                            
                            elif command == "save_contact":
                                # Save current chat partner as a contact
                                if partner_id:
                                    success = manager.save_contact(client_id, partner_id)
                                    
                                    if success:
                                        # Notify this user that the contact was saved
                                        save_message = {
                                            "type": "status",
                                            "status": "contact_saved",
                                            "message": f"User {partner_id} has been added to your contacts.",
                                            "timestamp": datetime.now().isoformat()
                                        }
                                        await websocket.send_text(json.dumps(save_message))
                                    else:
                                        # Contact already saved
                                        save_message = {
                                            "type": "status",
                                            "status": "contact_exists",
                                            "message": f"User {partner_id} is already in your contacts.",
                                            "timestamp": datetime.now().isoformat()
                                        }
                                        await websocket.send_text(json.dumps(save_message))
                        
                        elif message_data.get("type") == "typing":
                            # Handle typing indicator
                            is_typing = message_data.get("is_typing", False)
                            manager.set_typing_status(client_id, is_typing)
                            
                            if partner_id:
                                # Broadcast typing status to partner
                                await manager.broadcast_typing_status(client_id, partner_id)
                        
                        else:
                            # Regular chat message
                            message_data["id"] = str(uuid.uuid4())
                            message_data["timestamp"] = datetime.now().isoformat()
                            
                            if partner_id:
                                # We have a match, send the message to the partner
                                manager.add_to_chat_history(client_id, partner_id, message_data)
                                
                                # Send to partner
                                await manager.send_personal_message(json.dumps(message_data), partner_id)
                                
                                # Also send back to sender for confirmation with read status
                                message_data["read"] = False
                                await websocket.send_text(json.dumps(message_data))
                                
                                logger.info(f"Message from {client_id} to {partner_id}: {message_data.get('text', '')[:50]}...")
                            else:
                                # No match yet, send a waiting message
                                waiting_message = {
                                    "type": "status",
                                    "status": "waiting",
                                    "message": "Your message will be sent when someone joins the chat.",
                                    "timestamp": datetime.now().isoformat()
                                }
                                await websocket.send_text(json.dumps(waiting_message))
                    except json.JSONDecodeError:
                        error_msg = json.dumps({"error": "Invalid JSON format"})
                        await websocket.send_text(error_msg)
    except WebSocketDisconnect:
        # Cancel the match task if it's still running
        if match_task and not match_task.done():
            match_task.cancel()
        
        # End the chat if we were matched
        if partner_id:
            # Notify the partner that this user has left
            disconnect_message = {
                "type": "status",
                "status": "disconnected",
                "message": f"Your chat partner has disconnected.",
                "timestamp": datetime.now().isoformat()
            }
            await manager.send_personal_message(json.dumps(disconnect_message), partner_id)
            
            # End the chat in the matcher
            matcher.end_chat(client_id)
        else:
            # Cancel waiting if we weren't matched
            matcher.cancel_waiting(client_id)
        
        # Disconnect from the connection manager
        manager.disconnect(client_id)
    finally:
        # Make sure to clean up any tasks
        if match_task and not match_task.done():
            match_task.cancel()

@app.get("/api/read/{message_id}")
async def mark_as_read(message_id: str, user_id: str, partner_id: str):
    """Mark a message as read"""
    # Find the message in chat history
    chat_history = manager.get_chat_history(user_id, partner_id)
    
    for message in chat_history:
        if message.get("id") == message_id:
            message["read"] = True
            
            # Notify the sender that the message was read
            read_receipt = {
                "type": "read_receipt",
                "message_id": message_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send to the original sender
            sender_id = message.get("sender")
            if sender_id and sender_id in manager.active_connections:
                await manager.send_personal_message(json.dumps(read_receipt), sender_id)
            
            return {"status": "success"}
    
    return {"status": "error", "message": "Message not found"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting chat server with matching...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
