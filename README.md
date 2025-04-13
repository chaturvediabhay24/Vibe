# Chat Application with User Matching

A real-time chat application with a FastAPI backend and HTML/CSS/JavaScript frontend. The application matches users in real-time for one-on-one conversations with enhanced features for a better user experience.

## Features

- Real-time messaging using WebSockets
- Automatic user matching system
- User profiles with display name, interests, and age
- Typing indicators to see when your chat partner is typing
- Read receipts to know when your messages have been seen
- Skip functionality to find a new chat partner
- Save contacts to keep track of people you've chatted with
- Online status indicators for your saved contacts
- Message timestamps for better conversation tracking
- One-on-one private conversations
- User disconnect notifications
- Clean, responsive UI
- Separate frontend and backend architecture for easy extension
- Modular matching logic for future customization

## Project Structure

```
├── main.py                # FastAPI backend application
├── requirements.txt       # Python dependencies
├── matching/              # User matching module
│   ├── __init__.py        # Package initialization
│   └── matcher.py         # Matching logic
├── static/                # Static files directory
│   ├── css/               # CSS styles
│   │   └── styles.css     # Main stylesheet
│   └── js/                # JavaScript files
│       └── chat.js        # Chat functionality
└── templates/             # HTML templates
    └── index.html         # Main chat interface
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python main.py
```

The application will be available at http://localhost:8000

## How to Use

1. Open http://localhost:8000 in your browser
2. You'll see a loading spinner while the application waits for another user to join
3. Open another browser tab or window to http://localhost:8000
4. The two tabs will be automatically matched and can start chatting
5. Use the profile button to set up your user profile (display name, interests, age)
6. When chatting with someone, you can:
   - See when they're typing (typing indicator appears)
   - Know when they've read your messages (read receipts)
   - Skip to find a new chat partner using the Skip button
   - Save them as a contact using the Save Contact button
7. View your saved contacts by clicking the Contacts button
8. If one user closes their tab, the other user will be notified and returned to the waiting state

## API Endpoints

- `GET /`: Serves the main chat interface
- `WebSocket /ws/{client_id}`: WebSocket endpoint for real-time messaging
- `GET /api/stats`: Get application statistics (online users, active chats, waiting users)
- `POST /api/profile`: Update a user's profile
- `GET /api/profile/{user_id}`: Get a user's profile
- `POST /api/contacts/save`: Save a contact to a user's contact list
- `GET /api/contacts/{user_id}`: Get a user's saved contacts
- `GET /api/read/{message_id}`: Mark a message as read

## How It Works

- The backend uses FastAPI with WebSockets to handle real-time communication
- The matching module handles pairing users together for chat sessions
- When a user connects, they're placed in a waiting queue
- When another user connects, they're matched with the waiting user
- Messages are only sent between matched users
- The frontend shows a loading state while waiting for a match
- When matched, the chat interface becomes active
- Users can create profiles, save contacts, and see online status of contacts
- Typing indicators and read receipts enhance the chat experience

## Matching System

The matching system is implemented as a separate module that can be easily replaced or extended:

- `matching/matcher.py`: Contains the core matching logic
- The matcher maintains a queue of waiting users
- When a new user connects, they're matched with the first waiting user
- If no users are waiting, the new user is added to the waiting queue
- The matching logic can be customized to implement different matching strategies

## Extending with Next.js or Vue.js

The application is designed with a clear separation between the backend and frontend, making it easy to replace the frontend with a framework like Next.js or Vue.js:

### For Next.js:

1. Create a new Next.js project in a separate directory
2. Use the WebSocket API in your Next.js components to connect to the existing backend
3. Design your UI components based on the existing HTML/CSS structure
4. Configure CORS in the FastAPI backend to allow requests from your Next.js development server

### For Vue.js:

1. Create a new Vue.js project in a separate directory
2. Use the WebSocket API or a library like vue-socket.io in your Vue components
3. Design your UI components based on the existing HTML/CSS structure
4. Configure CORS in the FastAPI backend to allow requests from your Vue.js development server

## Future Enhancements

- Group chat functionality
- File sharing capabilities
- Voice and video chat integration
- Message search functionality
- User blocking capabilities
- Custom themes and appearance settings
- Mobile app using React Native or Flutter

## License

MIT
