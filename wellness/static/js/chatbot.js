document.addEventListener("DOMContentLoaded", function() {
    const chatMessages = document.getElementById("chatMessages");
    const userInput = document.getElementById("userInput");
    const sendBtn = document.getElementById("sendBtn");

    function appendMessage(sender, content) {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message');
        
        // Users get escaped text, bot gets formatted HTML (from backend or local formatter)
        msgDiv.innerHTML = `
            <div class="bubble">
                ${sender === 'user' ? `<p>${escapeHTML(content)}</p>` : formatText(content)}
            </div>
        `;

        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function showTypingIndicator() {
        const id = 'typing-' + Date.now();
        const msgDiv = document.createElement('div');
        msgDiv.id = id;
        msgDiv.classList.add('message', 'bot-message');
        
        msgDiv.innerHTML = `
            <div class="bubble">
                <div class="loading-dots">
                    <span class="dot"></span>
                    <span class="dot"></span>
                    <span class="dot"></span>
                </div>
            </div>
        `;

        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return id;
    }

    function removeMessage(id) {
        const element = document.getElementById(id);
        if (element) element.remove();
    }

    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
        );
    }

    function formatText(text) {
        // Simple markdown-style formatter as requested
        return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                   .split('\n\n').map(p => `<p>${p}</p>`).join('');
    }

    function handleSend() {
        const text = userInput.value.trim();
        if (text === "") return;

        appendMessage('user', text);
        userInput.value = "";
        sendBtn.disabled = true;
        
        const typingId = showTypingIndicator();
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        fetch('/chatbot/api/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ text: text })
        })
        .then(response => response.json())
        .then(data => {
            removeMessage(typingId);
            sendBtn.disabled = false;

            if (data.response) {
                appendMessage('bot', data.response);
            } else {
                appendMessage('bot', "I'm having a little trouble connecting right now. Please take a deep breath and try sharing that with me again in a moment.");
            }
        })
        .catch(error => {
            removeMessage(typingId);
            sendBtn.disabled = false;
            console.error('Error:', error);
            appendMessage('bot', "I'm having a little trouble connecting right now. Please take a deep breath and try sharing that with me again in a moment.");
        });
    }

    sendBtn.addEventListener("click", handleSend);
    userInput.addEventListener("keypress", function(e) {
        if (e.key === "Enter") {
            handleSend();
        }
    });

    // Scroll to bottom on load
    chatMessages.scrollTop = chatMessages.scrollHeight;
});
