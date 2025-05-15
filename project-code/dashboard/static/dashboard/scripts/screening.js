var isSending = false;
const chatContainer = document.getElementById('chatBox');
chatContainer.scrollTop = chatContainer.scrollHeight;

const waitingTextImage = document.createElement('div');
waitingTextImage.id = 'waitingTextImage';
waitingTextImage.innerHTML = '<img height="50" src="/static/dashboard/images/texting-wait.gif" alt="">';

function sendMessage() {
    if (isSending) return;
    isSending = true;
    const userInput = document.getElementById('userInput');
    const userMessage = userInput.value;
    if (userMessage.trim() === '') return;
    const userMessageElement = document.createElement('div');
    userMessageElement.className = 'message user';
    userMessageElement.textContent = userMessage;
    chatContainer.appendChild(userMessageElement);

    chatContainer.appendChild(waitingTextImage);

    userInput.value = '';

    chatContainer.scrollTop = chatContainer.scrollHeight;

    setTimeout(() => {
        sendMessageToServer(userMessage);
    }, 2000);
}
document.getElementById('userInput').addEventListener('keypress', function (event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
});

function sendMessageToServer(message) {
    let xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function () {
        if (xhr.readyState !== 4) return;
        if (xhr.status === 200) {
            addMessageToChat(xhr);
        } else {
            showErrorToast("Failed to send message. Please try again.");
            chatContainer.scrollTop = chatContainer.scrollHeight;
            isSending = false;
            chatContainer.removeChild(waitingTextImage);
        }
    };
    xhr.open("POST", "/api/sendChatConversation/", true);
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xhr.send(`message=${message}&csrfmiddlewaretoken=${getCSRFToken()}&patient_id=${patient_id}&screening_id=${screening_id}`);
}

function addMessageToChat(xhr) {
    // TODO process xhr to get hasConversationEnded and hide the chat box if true
    const hasConversationEnded = JSON.parse(xhr.responseText)["has_conversation_ended"];
    if (hasConversationEnded) {
        document.getElementById('chatBoxInput').style.display = 'none';
    }
    const botMessageElement = document.createElement('div');
    botMessageElement.className = 'message bot';
    botMessageElement.textContent = JSON.parse(xhr.responseText)["response_text"];
    chatContainer.appendChild(botMessageElement);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    isSending = false;
    chatContainer.removeChild(waitingTextImage);
}