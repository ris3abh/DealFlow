// main.js
document.addEventListener('DOMContentLoaded', function() {
    // Chat functionality
    const chatContainer = document.getElementById('chat-container');
    if (chatContainer) {
        initializeChat();
    }
    
    // Flash message auto-dismiss
    setTimeout(function() {
        const flashMessages = document.querySelectorAll('.flash-message');
        flashMessages.forEach(msg => {
            msg.style.opacity = '0';
            setTimeout(() => {
                msg.remove();
            }, 500);
        });
    }, 5000);
});

function initializeChat() {
    const messagesContainer = document.getElementById('messages-container');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const resetButton = document.getElementById('reset-button');
    const agentId = document.getElementById('agent-id').value;
    
    let isLoading = false;
    
    // Load conversation history
    loadMessages();
    
    // Send message when button is clicked
    sendButton.addEventListener('click', function() {
        sendMessage();
    });
    
    // Send message when Enter is pressed (without Shift)
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Reset agent
    if (resetButton) {
        resetButton.addEventListener('click', function() {
            if (confirm('Are you sure you want to reset? This will clear your current conversation and take you back to configuration.')) {
                fetch('/reset', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                })
                .then(response => response.json())
                .then(data => {
                    window.location.href = '/config';
                })
                .catch(error => {
                    console.error('Error resetting agent:', error);
                });
            }
        });
    }
    
    // Load messages from server
    function loadMessages() {
        fetch('/api/messages')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load messages');
                }
                return response.json();
            })
            .then(data => {
                displayMessages(data);
                scrollToBottom();
            })
            .catch(error => {
                console.error('Error loading messages:', error);
            });
    }
    
    // Send a message to the server
    function sendMessage() {
        const message = messageInput.value.trim();
        
        if (!message || isLoading) return;
        
        // Clear input and disable button
        messageInput.value = '';
        sendButton.disabled = true;
        isLoading = true;
        
        // Add user message to UI
        const messageList = document.getElementById('message-list');
        const userMessage = createMessageElement('user', message);
        messageList.appendChild(userMessage);
        scrollToBottom();
        
        // Add typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        typingIndicator.innerHTML = 'Agent is typing <span></span><span></span><span></span>';
        messageList.appendChild(typingIndicator);
        scrollToBottom();
        
        // Send to server
        fetch('/api/messages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to send message');
            }
            return response.json();
        })
        .then(data => {
            // Remove typing indicator
            messageList.removeChild(typingIndicator);
            
            // Add agent response
            const agentMessage = createMessageElement('agent', data.message);
            messageList.appendChild(agentMessage);
            scrollToBottom();
        })
        .catch(error => {
            console.error('Error sending message:', error);
            // Remove typing indicator
            if (typingIndicator.parentNode) {
                messageList.removeChild(typingIndicator);
            }
            
            // Show error message
            const errorMessage = document.createElement('div');
            errorMessage.className = 'flash-message flash-error';
            errorMessage.textContent = 'Failed to send message. Please try again.';
            messagesContainer.prepend(errorMessage);
            
            setTimeout(() => {
                errorMessage.remove();
            }, 5000);
        })
        .finally(() => {
            sendButton.disabled = false;
            isLoading = false;
        });
    }
    
    // Display messages in the UI
    function displayMessages(messages) {
        const messageList = document.getElementById('message-list');
        messageList.innerHTML = '';
        
        if (messages.length === 0) {
            const emptyState = document.createElement('div');
            emptyState.className = 'empty-state';
            emptyState.textContent = 'No messages yet. Start the conversation!';
            messageList.appendChild(emptyState);
            return;
        }
        
        messages.forEach(message => {
            const role = message.role === 'user' ? 'user' : 'agent';
            const messageEl = createMessageElement(role, message.content, message.timestamp);
            messageList.appendChild(messageEl);
        });
    }
    
    // Create a message element
    function createMessageElement(role, content, timestamp = new Date().toISOString()) {
        const messageEl = document.createElement('div');
        messageEl.className = `message message-${role}`;
        
        const contentEl = document.createElement('div');
        contentEl.className = 'message-content';
        contentEl.textContent = content;
        messageEl.appendChild(contentEl);
        
        const timeEl = document.createElement('div');
        timeEl.className = 'message-time';
        timeEl.textContent = formatTime(timestamp);
        messageEl.appendChild(timeEl);
        
        return messageEl;
    }
    
    // Format timestamp
    function formatTime(timestamp) {
        try {
            const date = new Date(timestamp);
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } catch (e) {
            return '';
        }
    }
    
    // Scroll to bottom of messages
    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}