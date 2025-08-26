const menuToggle = document.getElementById('menu-toggle');
        const navLinks = document.getElementById('nav-links');
        const chatMessages = document.getElementById('chat-messages');
        const chatInput = document.getElementById('chat-input');
        const typingIndicator = document.getElementById('typing-indicator');

        // Menu toggle functionality
        menuToggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
        });

        // Chatbot knowledge base
        const responses = {
            "how does travel together work": "Travel Together connects travelers with similar interests! 🌍 You can browse destinations, join travel groups, create your own trips, and connect with like-minded adventurers. Our platform makes it easy to find travel companions and plan amazing journeys together!",
            
            "how do i join a travel group": "Joining a group is simple! 👥 Go to the 'Groups' section, browse available trips, and click 'Join Group' on any that interest you. You can filter by destination, dates, group size, and interests to find your perfect travel match!",
            
            "what features are available": "We offer lots of exciting features! ✨\n• Browse and join travel groups\n• Create your own trips\n• User dashboard to manage your travels\n• Travel assistant for planning help\n• Chat with group members\n• Destination guides and tips\n• Safety and verification features",
            
            "how do i create an account": "Getting started is easy! 📝 Click the 'Sign Up' button (coming soon in User Dashboard), fill out your profile with travel preferences, interests, and a bit about yourself. Then you can start browsing groups and connecting with fellow travelers immediately!",
            
            "what is travel together": "Travel Together is a platform that connects travelers worldwide! 🌎 We help you find travel companions, join group trips, and create unforgettable experiences. Whether you're looking for adventure buddies, cultural explorers, or relaxation partners, we've got you covered!",
            
            "is it safe": "Safety is our top priority! 🛡️ We have user verification systems, reviews and ratings for travelers, secure messaging, and safety guidelines for all trips. We also provide emergency contacts and travel insurance recommendations for peace of mind.",
            
            "what destinations are available": "We cover destinations worldwide! 🗺️ From popular spots like Paris, Tokyo, and New York to off-the-beaten-path adventures in Nepal, Iceland, and Madagascar. Our travelers organize trips to every continent - where would you like to go?",
            
            "how much does it cost": "Joining Travel Together is free! 💰 You only pay for your own travel expenses (flights, hotels, activities) when you join a trip. Group organizers sometimes charge small coordination fees, but these are clearly stated upfront.",
            
            "hello": "Hello there! 👋 Welcome to Travel Together! I'm excited to help you discover amazing travel opportunities. What would you like to know about our platform?",
            
            "hi": "Hi! 😊 Great to meet you! I'm here to help you navigate Travel Together and find your next adventure. What questions do you have?",
            
            "help": "I'm here to help! 🤝 I can assist you with:\n• Understanding how Travel Together works\n• Finding and joining travel groups\n• Learning about our features\n• Account creation process\n• Safety information\n• Destination suggestions\n\nWhat would you like to know more about?"
        };

        function toggleChatbot() {
            const container = document.getElementById('chatbot-container');
            const isVisible = container.style.display === 'flex';
            container.style.display = isVisible ? 'none' : 'flex';
            
            if (!isVisible) {
                setTimeout(() => chatInput.focus(), 300);
            }
        }

        function openChatbot() {
            document.getElementById('chatbot-container').style.display = 'flex';
            setTimeout(() => chatInput.focus(), 300);
        }

        function closeChatbot() {
            document.getElementById('chatbot-container').style.display = 'none';
        }

        function sendMessage() {
            const message = chatInput.value.trim();
            if (!message) return;

            // Add user message
            addMessage(message, 'user');
            chatInput.value = '';

            // Show typing indicator
            showTyping();

            // Generate bot response
            setTimeout(() => {
                hideTyping();
                const response = generateResponse(message);
                addMessage(response, 'bot');
            }, 1000 + Math.random() * 1000);
        }

        function sendQuickMessage(message) {
            addMessage(message, 'user');
            showTyping();

            setTimeout(() => {
                hideTyping();
                const response = generateResponse(message);
                addMessage(response, 'bot');
            }, 800);
        }

        function addMessage(text, sender) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            messageDiv.textContent = text;
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function showTyping() {
            typingIndicator.style.display = 'block';
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function hideTyping() {
            typingIndicator.style.display = 'none';
        }

        function generateResponse(message) {
            const lowerMessage = message.toLowerCase();
            
            // Check for direct matches first
            for (const [key, response] of Object.entries(responses)) {
                if (lowerMessage.includes(key)) {
                    return response;
                }
            }
            
            // Check for keywords
            if (lowerMessage.includes('group') || lowerMessage.includes('join')) {
                return responses["how do i join a travel group"];
            }
            
            if (lowerMessage.includes('account') || lowerMessage.includes('sign up') || lowerMessage.includes('register')) {
                return responses["how do i create an account"];
            }
            
            if (lowerMessage.includes('safe') || lowerMessage.includes('security')) {
                return responses["is it safe"];
            }
            
            if (lowerMessage.includes('cost') || lowerMessage.includes('price') || lowerMessage.includes('money')) {
                return responses["how much does it cost"];
            }
            
            if (lowerMessage.includes('destination') || lowerMessage.includes('where') || lowerMessage.includes('place')) {
                return responses["what destinations are available"];
            }
            
            if (lowerMessage.includes('feature') || lowerMessage.includes('what can')) {
                return responses["what features are available"];
            }
            
            // Default responses for common patterns
            if (lowerMessage.includes('thank')) {
                return "You're welcome! 😊 I'm always here to help. Is there anything else you'd like to know about Travel Together?";
            }
            
            if (lowerMessage.includes('bye') || lowerMessage.includes('goodbye')) {
                return "Goodbye! 👋 Have an amazing day and happy travels! Feel free to come back anytime if you have more questions.";
            }
            
            // Default response
            return "I'd be happy to help! 🤔 Try asking me about how Travel Together works, joining groups, our features, creating an account, safety, or destinations. You can also use the quick action buttons below for common questions!";
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }

        // Show welcome animation on page load
        window.addEventListener('load', () => {
            setTimeout(() => {
                const toggle = document.getElementById('chatbot-toggle');
                toggle.style.animation = 'pulse 2s infinite';
            }, 2000);
        });