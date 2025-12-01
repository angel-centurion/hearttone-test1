// static/js/chatbot.js
class Chatbot {
    constructor() {
        this.messages = [];
        this.isLoading = false;
    }

    async sendMessage(message) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.addMessage('user', message);
        this.showLoading();
        
        try {
            const response = await fetch('/user/api/chatbot-analysis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.addMessage('bot', data.response);
            } else {
                this.addMessage('bot', '❌ Error: ' + (data.error || 'No se pudo conectar con el asistente'));
            }
        } catch (error) {
            this.addMessage('bot', '❌ Error de conexión. Intenta nuevamente.');
        } finally {
            this.hideLoading();
            this.isLoading = false;
        }
    }

    addMessage(sender, text) {
        const messagesContainer = document.getElementById('chatbot-messages');
        const messageClass = sender === 'user' ? 'alert-secondary' : 'alert-info';
        const alignment = sender === 'user' ? 'text-end' : '';
        
        const messageHtml = `
            <div class="alert ${messageClass} ${alignment}">
                <strong>${sender === 'user' ? 'Tú' : 'CardioBot'}:</strong><br>
                ${this.formatMessage(text)}
            </div>
        `;
        
        messagesContainer.innerHTML += messageHtml;
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    formatMessage(text) {
        // Convertir saltos de línea y formato básico
        return text.replace(/\n/g, '<br>')
                  .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                  .replace(/\*(.*?)\*/g, '<em>$1</em>');
    }

    showLoading() {
        const messagesContainer = document.getElementById('chatbot-messages');
        messagesContainer.innerHTML += `
            <div class="alert alert-warning">
                <strong>CardioBot:</strong> <i class="fas fa-spinner fa-spin"></i> Pensando...
            </div>
        `;
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    hideLoading() {
        const messagesContainer = document.getElementById('chatbot-messages');
        const lastMessage = messagesContainer.lastElementChild;
        if (lastMessage && lastMessage.querySelector('.fa-spinner')) {
            lastMessage.remove();
        }
    }
}

// Instancia global del chatbot
const chatbot = new Chatbot();

// Funciones globales para HTML
function sendChatMessage() {
    const input = document.getElementById('chatbot-input');
    const message = input.value.trim();
    
    if (message) {
        chatbot.sendMessage(message);
        input.value = '';
    }
}

function handleChatKeypress(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

function quickQuestion(question) {
    document.getElementById('chatbot-input').value = question;
    sendChatMessage();
}