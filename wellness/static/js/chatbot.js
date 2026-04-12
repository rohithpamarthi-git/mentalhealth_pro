document.addEventListener("DOMContentLoaded", function() {
    const chatMessages = document.getElementById("chatMessages");
    const userInput = document.getElementById("userInput");
    const sendBtn = document.getElementById("sendBtn");

    function appendMessage(text, isUser) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        msgDiv.innerHTML = `<p>${text}</p>`;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function handleSend() {
        const text = userInput.value.trim();
        if (text === "") return;

        appendMessage(text, true);
        userInput.value = "";
        
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
            if (data.response) {
                appendMessage(data.response, false);
            } else {
                appendMessage("Sorry, I encountered an error.", false);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            appendMessage("Sorry, I couldn't reach the server.", false);
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
