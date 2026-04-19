// Replace with your actual backend URL after deployment (e.g., https://your-backend.render.com)
const API_BASE_URL = window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';

let currentThreadId = null;

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const threadList = document.getElementById('thread-list');
const newChatBtn = document.getElementById('new-chat-btn');

// --- THREAD MANAGEMENT ---

async function loadThreads() {
    const response = await fetch(`${API_BASE_URL}/api/threads`);
    const threads = await response.json();
    
    threadList.innerHTML = '';
    threads.forEach(thread => {
        const div = document.createElement('div');
        div.className = `thread-item ${thread.thread_id === currentThreadId ? 'active' : ''}`;
        div.innerText = thread.title;
        div.onclick = () => switchThread(thread.thread_id);
        threadList.appendChild(div);
    });
}

async function createNewChat() {
    const response = await fetch(`${API_BASE_URL}/api/threads/new`, { method: 'POST' });
    const newThread = await response.json();
    currentThreadId = newThread.thread_id;
    
    // Clear chat area
    chatMessages.innerHTML = '';
    renderWelcomeCard();
    
    await loadThreads();
}

async function switchThread(threadId) {
    currentThreadId = threadId;
    
    const response = await fetch(`${API_BASE_URL}/api/history/${threadId}`);
    const history = await response.json();
    
    chatMessages.innerHTML = '';
    if (history.length === 0) {
        renderWelcomeCard();
    } else {
        history.forEach(msg => appendMessage(msg.role, msg.content));
    }
    
    await loadThreads();
}

function renderWelcomeCard() {
    const welcomeHtml = `
        <div class="welcome-card">
            <h1>📈 Mutual Fund FAQ Assistant</h1>
            <p>I provide objective data from official HDFC Mutual Fund documents.</p>
            <div class="example-questions">
                <button class="example-btn" onclick="sendExample('What is the exit load for HDFC Mid-Cap fund?')">What is the exit load for HDFC Mid-Cap fund?</button>
                <button class="example-btn" onclick="sendExample('Minimum SIP for HDFC Large Cap?')">Minimum SIP for HDFC Large Cap?</button>
                <button class="example-btn" onclick="sendExample('Lock-in for HDFC ELSS fund?')">Lock-in for HDFC ELSS fund?</button>
            </div>
        </div>
    `;
    chatMessages.innerHTML = welcomeHtml;
}

// --- CHAT LOGIC ---

async function sendMessage(text) {
    if (!text || !currentThreadId) return;

    // Check if it's the first message, if so clear welcome card
    if (chatMessages.querySelector('.welcome-card')) {
        chatMessages.innerHTML = '';
    }

    // Append User Message
    appendMessage('user', text);
    userInput.value = '';

    // Create Assistant Placeholder (Loading)
    const assistantMsgDiv = document.createElement('div');
    assistantMsgDiv.className = 'message assistant';
    assistantMsgDiv.innerHTML = `<div class="bubble">Typing...</div>`;
    chatMessages.appendChild(assistantMsgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, thread_id: currentThreadId })
        });
        
        const data = await response.json();
        
        // Replace "Typing..." with actual response
        assistantMsgDiv.querySelector('.bubble').innerText = data.response;
        
        // Refresh thread titles in sidebar
        await loadThreads();
        
    } catch (err) {
        assistantMsgDiv.querySelector('.bubble').innerText = "Oops! Something went wrong while connecting to the AI engine.";
    }
}

function appendMessage(role, content) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;
    msgDiv.innerHTML = `<div class="bubble">${content}</div>`;
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function sendExample(text) {
    sendMessage(text);
}

// --- EVENT LISTENERS ---

chatForm.onsubmit = (e) => {
    e.preventDefault();
    sendMessage(userInput.value);
};

newChatBtn.onclick = createNewChat;

// Initialize
(async () => {
    const response = await fetch(`${API_BASE_URL}/api/threads`);
    const threads = await response.json();
    if (threads.length > 0) {
        switchThread(threads[0].thread_id);
    } else {
        createNewChat();
    }
})();
