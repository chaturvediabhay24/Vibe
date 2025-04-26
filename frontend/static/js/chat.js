// Initialize WebSocket connection
const client_id = Date.now();
document.querySelector("#ws-id").textContent = client_id;
const ws = new WebSocket(`ws://localhost:8000/ws/${client_id}`);

// Message handling
ws.onmessage = function(event) {
    const messages = document.getElementById('messages');
    const message = createMessageElement(event.data, 'received');
    messages.appendChild(message);
    scrollToBottom();
};

// Create message element with proper styling
function createMessageElement(content, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    // Create timestamp
    const timestamp = new Date().toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    // Add message content
    messageDiv.innerHTML = `
        <div class="message-content">${content}</div>
        <div class="message-timestamp">${timestamp}</div>
    `;
    
    return messageDiv;
}

// Send message function
function sendMessage(event) {
    event.preventDefault();
    const input = document.getElementById("messageText");
    const content = input.value.trim();
    
    if (content) {
        // Send message through WebSocket
        ws.send(content);
        
        // Create and display sent message
        const messages = document.getElementById('messages');
        const message = createMessageElement(content, 'sent');
        messages.appendChild(message);
        
        // Clear input and scroll to bottom
        input.value = '';
        scrollToBottom();
    }
}

// Scroll to bottom of messages
function scrollToBottom() {
    const messagesContainer = document.querySelector('.messages-container');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Add typing animation
const messageInput = document.getElementById('messageText');
let typingTimeout;

messageInput.addEventListener('input', () => {
    clearTimeout(typingTimeout);
    // Here you could add code to show "User is typing..." status
    
    typingTimeout = setTimeout(() => {
        // Here you could add code to clear "User is typing..." status
    }, 1000);
});

// Handle connection status
ws.onopen = () => {
    console.log('Connected to chat server');
    const statusDot = document.querySelector('.status-dot');
    statusDot.style.background = '#4ade80';
};

ws.onclose = () => {
    console.log('Disconnected from chat server');
    const statusDot = document.querySelector('.status-dot');
    statusDot.style.background = '#ef4444';
};

// Handle emoji shortcuts
messageInput.addEventListener('keyup', (e) => {
    const shortcuts = {
        ':)': '😊',
        ':(': '😢',
        ':D': '😃',
        '<3': '❤️',
        ':p': '😛',
        ';)': '😉'
    };
    
    for (let shortcut in shortcuts) {
        if (messageInput.value.includes(shortcut)) {
            messageInput.value = messageInput.value.replace(shortcut, shortcuts[shortcut]);
        }
    }
});
