// In /static/group_chat.js

document.addEventListener('DOMContentLoaded', () => {
    // 1. Establish a WebSocket connection
    const socket = io();

    // Get elements from the page
    const chatForm = document.getElementById('chat-form');
    const messageInput = chatForm.querySelector('input[name="message"]');
    const messagesContainer = document.getElementById('messages');
    
    // Extract group_id and username from the HTML (rendered by Flask)
    const groupId = document.body.dataset.groupId;
    const currentUsername = document.body.dataset.username;

    // 2. Join the specific group chat room
    if (groupId) {
        socket.emit('join_room', { 'group_id': groupId });
        console.log(`Socket attempting to join room: ${groupId}`);
    }

    // 3. Handle form submission to SEND a message
    chatForm.addEventListener('submit', (e) => {
        // Prevent the page from reloading
        e.preventDefault();

        const messageText = messageInput.value.trim();
        if (messageText && groupId) {
            // This is an API call, not a WebSocket emit, based on your app.py
            fetch(`/api/messages/send/${groupId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: messageText })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Clear input only after successful send
                    messageInput.value = '';
                } else {
                    console.error('Failed to send message:', data.message);
                }
            })
            .catch(err => console.error('Error sending message:', err));
        }
    });

    // 4. Listen for new messages to DISPLAY them
    socket.on('new_message', (data) => {
        const messageElement = document.createElement('div');
        // Add a class to style messages from the current user differently
        const messageSide = data.sender_name === currentUsername ? 'sent' : 'received';
        
        messageElement.classList.add('message', messageSide);
        messageElement.innerHTML = `<strong>${data.sender_name}</strong><p>${data.message}</p>`;

        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    });

    // Ensure the view is scrolled to the bottom on load
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
});