document.addEventListener('DOMContentLoaded', () => {
    // Generate a unique client ID for this tab
    const clientId = 'user_' + Math.random().toString(36).substr(2, 9);
    
    // DOM Elements
    const messagesContainer = document.getElementById('messages');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const connectionStatus = document.getElementById('connection-status');
    const chatStatus = document.getElementById('chat-status');
    const userIdElement = document.getElementById('user-id');
    const partnerInfo = document.getElementById('partner-info');
    const loadingContainer = document.getElementById('loading-container');
    
    // Create UI elements for new features
    createUIElements();
    
    // Chat state
    let chatState = 'waiting'; // waiting, matched, disconnected
    let partnerId = null;
    let typingTimeout = null;
    let userProfile = {};
    let savedContacts = [];
    
    // Display the client ID
    userIdElement.textContent = clientId;
    
    // WebSocket connection
    let ws = null;
    
    // Connect WebSocket
    function connectWebSocket() {
        // Determine WebSocket protocol (ws or wss)
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsBase = `${protocol}//${window.location.host}/ws`;
        
        // Connect WebSocket
        ws = new WebSocket(`${wsBase}/${clientId}`);
        setupWebSocket(ws);
    }
    
    // Setup WebSocket event handlers
    function setupWebSocket(ws) {
        ws.onopen = () => {
            console.log('WebSocket connected');
            connectionStatus.textContent = 'Connected';
            connectionStatus.classList.add('connected');
            connectionStatus.classList.remove('disconnected');
            
            // Load user profile and contacts
            loadUserProfile();
            loadContacts();
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleMessage(data);
        };
        
        ws.onclose = () => {
            console.log('WebSocket disconnected');
            connectionStatus.textContent = 'Disconnected';
            connectionStatus.classList.add('disconnected');
            connectionStatus.classList.remove('connected');
            
            // Update chat state
            updateChatState('disconnected', 'Connection lost. Trying to reconnect...');
            
            // Try to reconnect after a delay
            setTimeout(() => {
                connectWebSocket();
            }, 3000);
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            connectionStatus.textContent = 'Error';
            connectionStatus.classList.add('disconnected');
            connectionStatus.classList.remove('connected');
        };
    }
    
    // Create UI elements for new features
    function createUIElements() {
        // Create chat controls container
        const chatControls = document.createElement('div');
        chatControls.className = 'chat-controls';
        
        // Skip button
        const skipButton = document.createElement('button');
        skipButton.id = 'skip-button';
        skipButton.className = 'control-button';
        skipButton.textContent = 'Skip';
        skipButton.title = 'Skip this chat and find a new partner';
        skipButton.disabled = true;
        skipButton.addEventListener('click', skipChat);
        
        // Save contact button
        const saveContactButton = document.createElement('button');
        saveContactButton.id = 'save-contact-button';
        saveContactButton.className = 'control-button';
        saveContactButton.textContent = 'Save Contact';
        saveContactButton.title = 'Save this user to your contacts';
        saveContactButton.disabled = true;
        saveContactButton.addEventListener('click', saveContact);
        
        // Profile button
        const profileButton = document.createElement('button');
        profileButton.id = 'profile-button';
        profileButton.className = 'control-button';
        profileButton.textContent = 'Profile';
        profileButton.title = 'Edit your profile';
        profileButton.addEventListener('click', showProfileModal);
        
        // Contacts button
        const contactsButton = document.createElement('button');
        contactsButton.id = 'contacts-button';
        contactsButton.className = 'control-button';
        contactsButton.textContent = 'Contacts';
        contactsButton.title = 'View your saved contacts';
        contactsButton.addEventListener('click', showContactsModal);
        
        // Add buttons to controls
        chatControls.appendChild(skipButton);
        chatControls.appendChild(saveContactButton);
        chatControls.appendChild(profileButton);
        chatControls.appendChild(contactsButton);
        
        // Add typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.id = 'typing-indicator';
        typingIndicator.className = 'typing-indicator';
        typingIndicator.style.display = 'none';
        typingIndicator.innerHTML = '<span>Partner is typing</span><span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>';
        
        // Add elements to the page
        const chatScreen = document.querySelector('.chat-screen');
        const inputContainer = document.querySelector('.input-container');
        
        // Insert controls before the input container
        chatScreen.insertBefore(chatControls, inputContainer);
        
        // Insert typing indicator before the input container
        chatScreen.insertBefore(typingIndicator, inputContainer);
        
        // Create modals
        createProfileModal();
        createContactsModal();
    }
    
    // Create profile modal
    function createProfileModal() {
        const modal = document.createElement('div');
        modal.id = 'profile-modal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <span class="close-button">&times;</span>
                <h2>Your Profile</h2>
                <form id="profile-form">
                    <div class="form-group">
                        <label for="display-name">Display Name:</label>
                        <input type="text" id="display-name" name="display-name" placeholder="Enter a display name">
                    </div>
                    <div class="form-group">
                        <label for="interests">Interests (comma separated):</label>
                        <input type="text" id="interests" name="interests" placeholder="e.g. music, movies, travel">
                    </div>
                    <div class="form-group">
                        <label for="age">Age:</label>
                        <input type="number" id="age" name="age" min="13" max="120">
                    </div>
                    <button type="submit" class="submit-button">Save Profile</button>
                </form>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Close button functionality
        const closeButton = modal.querySelector('.close-button');
        closeButton.addEventListener('click', () => {
            modal.style.display = 'none';
        });
        
        // Close when clicking outside the modal
        window.addEventListener('click', (event) => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
        
        // Form submission
        const form = modal.querySelector('#profile-form');
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            saveProfile();
        });
    }
    
    // Create contacts modal
    function createContactsModal() {
        const modal = document.createElement('div');
        modal.id = 'contacts-modal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <span class="close-button">&times;</span>
                <h2>Your Contacts</h2>
                <div id="contacts-list" class="contacts-list">
                    <p>No contacts saved yet.</p>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Close button functionality
        const closeButton = modal.querySelector('.close-button');
        closeButton.addEventListener('click', () => {
            modal.style.display = 'none';
        });
        
        // Close when clicking outside the modal
        window.addEventListener('click', (event) => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    }
    
    // Show profile modal
    function showProfileModal() {
        const modal = document.getElementById('profile-modal');
        
        // Fill in existing profile data if available
        const displayNameInput = document.getElementById('display-name');
        const interestsInput = document.getElementById('interests');
        const ageInput = document.getElementById('age');
        
        displayNameInput.value = userProfile.display_name || '';
        interestsInput.value = userProfile.interests ? userProfile.interests.join(', ') : '';
        ageInput.value = userProfile.age || '';
        
        modal.style.display = 'block';
    }
    
    // Show contacts modal
    function showContactsModal() {
        const modal = document.getElementById('contacts-modal');
        
        // Refresh contacts list
        loadContacts();
        
        modal.style.display = 'block';
    }
    
    // Save profile
    function saveProfile() {
        const displayName = document.getElementById('display-name').value;
        const interests = document.getElementById('interests').value;
        const age = document.getElementById('age').value;
        
        // Create form data
        const formData = new FormData();
        formData.append('user_id', clientId);
        
        if (displayName) formData.append('display_name', displayName);
        if (interests) formData.append('interests', interests);
        if (age) formData.append('age', age);
        
        // Send to server
        fetch('/api/profile', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            userProfile = data;
            
            // Close modal
            document.getElementById('profile-modal').style.display = 'none';
            
            // Show confirmation
            displayStatusMessage('Profile updated successfully', 'success');
        })
        .catch(error => {
            console.error('Error updating profile:', error);
            displayErrorMessage('Failed to update profile');
        });
    }
    
    // Load user profile
    function loadUserProfile() {
        fetch(`/api/profile/${clientId}`)
            .then(response => response.json())
            .then(data => {
                if (!data.error) {
                    userProfile = data;
                }
            })
            .catch(error => {
                console.error('Error loading profile:', error);
            });
    }
    
    // Load contacts
    function loadContacts() {
        fetch(`/api/contacts/${clientId}`)
            .then(response => response.json())
            .then(data => {
                savedContacts = data;
                updateContactsList();
            })
            .catch(error => {
                console.error('Error loading contacts:', error);
            });
    }
    
    // Update contacts list in the modal
    function updateContactsList() {
        const contactsList = document.getElementById('contacts-list');
        
        if (savedContacts.length === 0) {
            contactsList.innerHTML = '<p>No contacts saved yet.</p>';
            return;
        }
        
        let html = '';
        
        savedContacts.forEach(contact => {
            const displayName = contact.profile.display_name || `User ${contact.id}`;
            const onlineStatus = contact.online ? 'online' : 'offline';
            
            html += `
                <div class="contact-item">
                    <div class="contact-info">
                        <span class="contact-name">${displayName}</span>
                        <span class="contact-status ${onlineStatus}">${onlineStatus}</span>
                    </div>
                </div>
            `;
        });
        
        contactsList.innerHTML = html;
    }
    
    // Skip current chat
    function skipChat() {
        if (chatState !== 'matched') return;
        
        const commandData = {
            type: 'command',
            command: 'skip',
            sender: clientId,
            timestamp: new Date().toISOString()
        };
        
        ws.send(JSON.stringify(commandData));
    }
    
    // Save current chat partner as contact
    function saveContact() {
        if (chatState !== 'matched' || !partnerId) return;
        
        const commandData = {
            type: 'command',
            command: 'save_contact',
            sender: clientId,
            timestamp: new Date().toISOString()
        };
        
        ws.send(JSON.stringify(commandData));
    }
    
    // Handle incoming messages
    function handleMessage(data) {
        console.log('Received message:', data);
        
        // Check message type
        if (data.type === 'status') {
            handleStatusMessage(data);
        } else if (data.type === 'typing_status') {
            handleTypingStatus(data);
        } else if (data.type === 'read_receipt') {
            handleReadReceipt(data);
        } else if (data.type === 'contact_status') {
            handleContactStatus(data);
        } else if (data.error) {
            // Handle error messages
            displayErrorMessage(data.error);
        } else {
            // Regular chat message
            displayChatMessage(data);
            
            // Mark message as read if it's from partner
            if (data.sender !== clientId && data.id) {
                markMessageAsRead(data.id);
            }
        }
    }
    
    // Handle typing status
    function handleTypingStatus(data) {
        const typingIndicator = document.getElementById('typing-indicator');
        
        if (data.is_typing) {
            typingIndicator.style.display = 'block';
        } else {
            typingIndicator.style.display = 'none';
        }
    }
    
    // Handle read receipt
    function handleReadReceipt(data) {
        // Find the message element by ID and update its status
        const messageId = data.message_id;
        const messageElement = document.querySelector(`.message[data-id="${messageId}"]`);
        
        if (messageElement) {
            messageElement.classList.add('read');
            
            // Update read indicator if it exists
            const readIndicator = messageElement.querySelector('.read-indicator');
            if (readIndicator) {
                readIndicator.textContent = 'Read';
                readIndicator.classList.add('read');
            }
        }
    }
    
    // Handle contact status update
    function handleContactStatus(data) {
        // Update contact status in the contacts list
        loadContacts();
        
        // Show notification if a contact comes online
        if (data.status === 'online') {
            const contactInfo = savedContacts.find(c => c.id === data.contact_id);
            const displayName = contactInfo?.profile?.display_name || `User ${data.contact_id}`;
            
            displayStatusMessage(`${displayName} is now online`, 'contact-online');
        }
    }
    
    // Handle status messages
    function handleStatusMessage(data) {
        switch (data.status) {
            case 'waiting':
                updateChatState('waiting', data.message);
                break;
            case 'matched':
                partnerId = data.partnerId;
                updateChatState('matched', data.message);
                break;
            case 'disconnected':
                partnerId = null;
                updateChatState('disconnected', data.message);
                break;
            case 'skipped':
                partnerId = null;
                updateChatState('waiting', data.message);
                break;
            case 'contact_saved':
            case 'contact_exists':
                // Just display the message, don't change state
                displayStatusMessage(data.message, data.status);
                // Refresh contacts
                loadContacts();
                break;
            default:
                console.warn('Unknown status:', data.status);
        }
        
        // Display the status message in the chat
        if (['waiting', 'matched', 'disconnected', 'skipped'].includes(data.status)) {
            displayStatusMessage(data.message, data.status);
        }
    }
    
    // Update the chat state
    function updateChatState(state, statusText) {
        chatState = state;
        chatStatus.textContent = statusText || getStatusText(state);
        chatStatus.className = ''; // Clear existing classes
        chatStatus.classList.add(state);
        
        // Update UI based on state
        const skipButton = document.getElementById('skip-button');
        const saveContactButton = document.getElementById('save-contact-button');
        const typingIndicator = document.getElementById('typing-indicator');
        
        // Update partner info
        if (state === 'matched' && partnerId) {
            partnerInfo.textContent = `Chatting with User ${partnerId}`;
            loadingContainer.style.display = 'none';
            
            // Enable input and buttons
            messageInput.disabled = false;
            sendButton.disabled = false;
            skipButton.disabled = false;
            saveContactButton.disabled = false;
            messageInput.focus();
        } else if (state === 'waiting') {
            partnerInfo.textContent = 'Waiting for someone to join...';
            loadingContainer.style.display = 'flex';
            
            // Disable input and buttons
            messageInput.disabled = true;
            sendButton.disabled = true;
            skipButton.disabled = true;
            saveContactButton.disabled = true;
            typingIndicator.style.display = 'none';
        } else if (state === 'disconnected') {
            partnerInfo.textContent = 'Disconnected';
            loadingContainer.style.display = 'none';
            
            // Disable input and buttons
            messageInput.disabled = true;
            sendButton.disabled = true;
            skipButton.disabled = true;
            saveContactButton.disabled = true;
            typingIndicator.style.display = 'none';
        }
    }
    
    // Get status text based on state
    function getStatusText(state) {
        switch (state) {
            case 'waiting': return 'Waiting for a match...';
            case 'matched': return 'Chatting';
            case 'disconnected': return 'Disconnected';
            default: return 'Unknown';
        }
    }
    
    // Display a status message in the chat
    function displayStatusMessage(text, status) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('status-message');
        
        if (status) {
            messageElement.classList.add(status);
        }
        
        // Add timestamp
        const timestamp = new Date().toLocaleTimeString();
        const timestampElement = document.createElement('span');
        timestampElement.classList.add('timestamp');
        timestampElement.textContent = timestamp;
        
        const textElement = document.createElement('span');
        textElement.textContent = text;
        
        messageElement.appendChild(textElement);
        messageElement.appendChild(timestampElement);
        
        // Add message to container
        messagesContainer.appendChild(messageElement);
        
        // Scroll to the bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // Display an error message
    function displayErrorMessage(text) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('status-message', 'disconnected');
        messageElement.textContent = `Error: ${text}`;
        
        // Add message to container
        messagesContainer.appendChild(messageElement);
        
        // Scroll to the bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // Display a chat message
    function displayChatMessage(data) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        
        // Store message ID for read receipts
        if (data.id) {
            messageElement.setAttribute('data-id', data.id);
        }
        
        // Check if this is a system message
        if (data.sender === 'system') {
            // Create a system notification
            messageElement.classList.add('system-message');
            messageElement.textContent = data.text;
        } else {
            // Regular user message
            // Determine if the message was sent by this client or received from another
            const isSent = data.sender === clientId;
            messageElement.classList.add(isSent ? 'message-sent' : 'message-received');
            
            // Create message content
            const messageContent = document.createElement('div');
            messageContent.classList.add('message-content');
            messageContent.textContent = data.text;
            
            // Create message info (timestamp, read status)
            const messageInfo = document.createElement('div');
            messageInfo.classList.add('message-info');
            
            // Add timestamp
            const timestamp = data.timestamp 
                ? new Date(data.timestamp).toLocaleTimeString() 
                : new Date().toLocaleTimeString();
            
            const timestampElement = document.createElement('span');
            timestampElement.classList.add('timestamp');
            timestampElement.textContent = timestamp;
            messageInfo.appendChild(timestampElement);
            
            // Add read indicator for sent messages
            if (isSent) {
                const readIndicator = document.createElement('span');
                readIndicator.classList.add('read-indicator');
                readIndicator.textContent = data.read ? 'Read' : 'Sent';
                
                if (data.read) {
                    readIndicator.classList.add('read');
                    messageElement.classList.add('read');
                }
                
                messageInfo.appendChild(readIndicator);
            }
            
            // Add content and info to message
            messageElement.appendChild(messageContent);
            messageElement.appendChild(messageInfo);
        }
        
        // Add message to container
        messagesContainer.appendChild(messageElement);
        
        // Scroll to the bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // Mark message as read
    function markMessageAsRead(messageId) {
        if (!messageId || !partnerId) return;
        
        fetch(`/api/read/${messageId}?user_id=${clientId}&partner_id=${partnerId}`)
            .catch(error => {
                console.error('Error marking message as read:', error);
            });
    }
    
    // Send a message
    function sendMessage(text) {
        if (!text.trim()) return;
        if (chatState !== 'matched') return;
        
        const messageData = {
            text: text,
            sender: clientId,
            timestamp: new Date().toISOString()
        };
        
        ws.send(JSON.stringify(messageData));
    }
    
    // Send typing indicator
    function sendTypingIndicator(isTyping) {
        if (chatState !== 'matched') return;
        
        const typingData = {
            type: 'typing',
            is_typing: isTyping,
            sender: clientId,
            timestamp: new Date().toISOString()
        };
        
        ws.send(JSON.stringify(typingData));
    }
    
    // Event listener for send button
    sendButton.addEventListener('click', () => {
        sendMessage(messageInput.value);
        messageInput.value = '';
        messageInput.focus();
        
        // Clear typing indicator
        sendTypingIndicator(false);
    });
    
    // Event listener for enter key in input field
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage(messageInput.value);
            messageInput.value = '';
            
            // Clear typing indicator
            sendTypingIndicator(false);
        }
    });
    
    // Event listener for typing
    messageInput.addEventListener('input', () => {
        // Clear previous timeout
        if (typingTimeout) {
            clearTimeout(typingTimeout);
        }
        
        // Send typing indicator
        sendTypingIndicator(true);
        
        // Set timeout to clear typing indicator after 2 seconds of inactivity
        typingTimeout = setTimeout(() => {
            sendTypingIndicator(false);
        }, 2000);
    });
    
    // Event listener for blur (user stops focusing on input)
    messageInput.addEventListener('blur', () => {
        // Clear typing indicator
        sendTypingIndicator(false);
        
        if (typingTimeout) {
            clearTimeout(typingTimeout);
        }
    });
    
    // Initialize the chat state
    updateChatState('waiting');
    
    // Connect WebSocket when the page loads
    connectWebSocket();
    
    // Add CSS for new features
    addStyles();
    
    // Function to add CSS for new features
    function addStyles() {
        const styleElement = document.createElement('style');
        styleElement.textContent = `
            /* Chat controls */
            .chat-controls {
                display: flex;
                justify-content: space-between;
                padding: 10px;
                background-color: #f0f0f0;
                border-top: 1px solid #ddd;
            }
            
            .control-button {
                padding: 8px 12px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                transition: background-color 0.3s;
            }
            
            .control-button:hover:not(:disabled) {
                background-color: #2980b9;
            }
            
            .control-button:disabled {
                background-color: #a0cfee;
                cursor: not-allowed;
            }
            
            /* Typing indicator */
            .typing-indicator {
                padding: 8px 12px;
                font-style: italic;
                color: #666;
                background-color: #f9f9f9;
                border-top: 1px solid #eee;
            }
            
            .typing-indicator .dot {
                animation: typing 1.5s infinite;
                display: inline-block;
            }
            
            .typing-indicator .dot:nth-child(2) {
                animation-delay: 0.2s;
            }
            
            .typing-indicator .dot:nth-child(3) {
                animation-delay: 0.4s;
            }
            
            @keyframes typing {
                0% { opacity: 0.3; }
                50% { opacity: 1; }
                100% { opacity: 0.3; }
            }
            
            /* Message enhancements */
            .message-content {
                margin-bottom: 4px;
            }
            
            .message-info {
                display: flex;
                justify-content: space-between;
                font-size: 0.7em;
                color: #888;
            }
            
            .timestamp {
                margin-left: 8px;
                font-size: 0.7em;
                color: #888;
            }
            
            .read-indicator {
                font-style: italic;
            }
            
            .read-indicator.read {
                color: #27ae60;
            }
            
            /* Modal styles */
            .modal {
                display: none;
                position: fixed;
                z-index: 100;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
            }
            
            .modal-content {
                background-color: white;
                margin: 10% auto;
                padding: 20px;
                border-radius: 8px;
                width: 80%;
                max-width: 500px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                position: relative;
            }
            
            .close-button {
                position: absolute;
                top: 10px;
                right: 15px;
                font-size: 24px;
                font-weight: bold;
                cursor: pointer;
            }
            
            /* Form styles */
            .form-group {
                margin-bottom: 15px;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }
            
            .form-group input {
                width: 100%;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            
            .submit-button {
                padding: 10px 15px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                transition: background-color 0.3s;
            }
            
            .submit-button:hover {
                background-color: #2980b9;
            }
            
            /* Contacts list */
            .contacts-list {
                max-height: 300px;
                overflow-y: auto;
            }
            
            .contact-item {
                padding: 10px;
                border-bottom: 1px solid #eee;
            }
            
            .contact-info {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .contact-name {
                font-weight: bold;
            }
            
            .contact-status {
                padding: 3px 6px;
                border-radius: 10px;
                font-size: 0.8em;
            }
            
            .contact-status.online {
                background-color: #d4edda;
                color: #155724;
            }
            
            .contact-status.offline {
                background-color: #f8d7da;
                color: #721c24;
            }
            
            /* Status message enhancements */
            .status-message.contact-online {
                background-color: #d4edda;
                color: #155724;
            }
            
            .status-message.contact-saved,
            .status-message.success {
                background-color: #d1ecf1;
                color: #0c5460;
            }
            
            .status-message.contact-exists {
                background-color: #fff3cd;
                color: #856404;
            }
            
            .status-message.skipped {
                background-color: #f8d7da;
                color: #721c24;
            }
        `;
        
        document.head.appendChild(styleElement);
    }
});
