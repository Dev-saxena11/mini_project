document.addEventListener('DOMContentLoaded', () => {
    // === DOM Element Selectors ===
    const menuToggle = document.getElementById('menu-toggle');
    const navLinks = document.getElementById('nav-links');
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const typingIndicator = document.getElementById('typing-indicator');
    const chatbotContainer = document.getElementById('chatbot-container');
    const quickActions = document.getElementById('quick-actions');
    const clearChatBtn = document.getElementById('clear-chat-btn');

    // === State ===
    let chatHistory = [];
    let quickActionsVisible = true;

    // === Chatbot Knowledge Base ===
    const responses = {
        "how it works": "Travel Together connects travelers! 🌍 You can browse destinations, join or create groups, and connect with like-minded adventurers to plan amazing journeys together!",
        "join groups": "It's simple! 👥 Go to the 'Groups' section, find a trip that interests you, and click 'Join Group'. You can find your perfect travel match!",
        "features": "We offer lots of features! ✨ Browse and join groups, create your own trips, a user dashboard, this travel assistant, and group chats!",
        "default": "I can help with that! 🤔 Try asking about how Travel Together works, joining groups, or our features. You can also use the quick action buttons."
    };

    // === Event Listeners ===
    if (menuToggle) menuToggle.addEventListener('click', () => navLinks.classList.toggle('active'));
    if (clearChatBtn) clearChatBtn.addEventListener('click', clearChat);

    // === Functions ===

    /** Toggles the chatbot's visibility */
    window.toggleChatbot = () => {
        const isVisible = chatbotContainer.style.display === 'flex';
        chatbotContainer.style.display = isVisible ? 'none' : 'flex';
        if (!isVisible) setTimeout(() => chatInput.focus(), 300);
    };
    
    /** Opens the chatbot */
    window.openChatbot = () => {
        chatbotContainer.style.display = 'flex';
        setTimeout(() => chatInput.focus(), 300);
    };

    /** Closes the chatbot */
    window.closeChatbot = () => {
        chatbotContainer.style.display = 'none';
    };

    /** Handles the enter key press in the input field */
    window.handleKeyPress = (event) => {
        if (event.key === 'Enter') sendMessage();
    };
    
    /** Sends a message from the text input */
    window.sendMessage = () => {
        const messageText = chatInput.value.trim();
        if (!messageText) return;
        
        addMessage(messageText, 'user');
        chatInput.value = '';
        if (quickActionsVisible) {
            quickActions.style.display = 'none';
            quickActionsVisible = false;
        }
        
        generateBotResponse(messageText);
    };
    
    /** Sends a message from a quick action button */
    window.sendQuickMessage = (messageText) => {
        addMessage(messageText, 'user');
        if (quickActionsVisible) {
            quickActions.style.display = 'none';
            quickActionsVisible = false;
        }
        generateBotResponse(messageText);
    };

    /**
     * Creates and adds a message to the UI and history.
     * @param {string} text - The message content.
     * @param {string} sender - 'user' or 'bot'.
     * @param {string} [timestamp=now] - Optional timestamp for loading history.
     */
    function addMessage(text, sender, timestamp = new Date().toISOString()) {
        const messageData = { text, sender, timestamp };
        chatHistory.push(messageData);
        saveChatHistory();

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const textNode = document.createElement('p');
        textNode.textContent = text;
        
        const timeNode = document.createElement('small');
        timeNode.className = 'message-timestamp';
        timeNode.textContent = new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        messageDiv.appendChild(textNode);
        messageDiv.appendChild(timeNode);
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    /** Simulates the bot's response generation */
    function generateBotResponse(userMessage) {
        showTyping();
        setTimeout(() => {
            hideTyping();
            const lowerMessage = userMessage.toLowerCase();
            let response = responses.default; // Default response
            for (const key in responses) {
                if (lowerMessage.includes(key)) {
                    response = responses[key];
                    break;
                }
            }
            addMessage(response, 'bot');
        }, 1200);
    }
    
    /** Clears the chat UI, history, and local storage */
    function clearChat() {
        chatMessages.innerHTML = '';
        chatHistory = [];
        localStorage.removeItem('chatHistory');
        addMessage("Hello! 👋 How can I help you plan your next adventure?", 'bot');
        if (!quickActionsVisible) {
            quickActions.style.display = 'flex';
            quickActionsVisible = true;
        }
    }

    // --- Utility Functions ---
    function showTyping() {
        typingIndicator.style.display = 'flex';
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    function hideTyping() { typingIndicator.style.display = 'none'; }
    function saveChatHistory() { localStorage.setItem('chatHistory', JSON.stringify(chatHistory)); }

    /** Loads chat history from local storage on page load */
    function loadChatHistory() {
        const savedHistory = localStorage.getItem('chatHistory');
        if (savedHistory) {
            chatHistory = JSON.parse(savedHistory);
            chatMessages.innerHTML = ''; // Clear any static content
            chatHistory.forEach(msg => {
                // Re-render message without adding to history again
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${msg.sender}-message`;
                const textNode = document.createElement('p');
                textNode.textContent = msg.text;
                const timeNode = document.createElement('small');
                timeNode.className = 'message-timestamp';
                timeNode.textContent = new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                messageDiv.appendChild(textNode);
                messageDiv.appendChild(timeNode);
                chatMessages.appendChild(messageDiv);
            });
            chatMessages.scrollTop = chatMessages.scrollHeight;

            if(chatHistory.length > 1) { // If there's more than the welcome message
                 quickActions.style.display = 'none';
                 quickActionsVisible = false;
            }
        } else {
            // If no history, add the initial bot message
            addMessage("Hello! 👋 How can I help you plan your next adventure?", 'bot');
        }
    }

    // --- Initial Load ---
    loadChatHistory();
});