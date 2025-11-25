/**
 * static/script.js
 * * Client-side logic for the MJU AI Assistant.
 * Handles chat interactions, API communication, and UI responsiveness.
 */

// Configuration
const API_ENDPOINT = '/chat';

/**
 * Sends the user's message to the backend API and updates the chat UI.
 * Triggered by the send button click or the 'Enter' key press.
 * * Flow:
 * 1. Validate input.
 * 2. Display user message immediately.
 * 3. Show loading indicator.
 * 4. Fetch response from server.
 * 5. Render markdown response.
 */
async function sendMessage() {
    const inputField = document.getElementById('user-input');
    const message = inputField.value.trim();

    // Prevent sending empty messages
    if (!message) return;

    const chatBox = document.getElementById('chat-box');
    const sendBtn = document.getElementById('send-btn');
    const loading = document.getElementById('loading');

    // 1. Display User Message
    // Use escapeHtml to prevent XSS attacks from user input
    chatBox.innerHTML += `<div class="message user">${escapeHtml(message)}</div>`;
    inputField.value = '';
    scrollToBottom();

    // 2. Set Loading State
    sendBtn.disabled = true;
    chatBox.appendChild(loading); // Move loading indicator to the bottom
    loading.style.display = 'block';
    scrollToBottom();

    try {
        // 3. API Request
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });
        
        const data = await response.json();
        
        // 4. Hide Loading
        loading.style.display = 'none';
        
        // 5. Render Bot Response
        // Check for errors in response or use the successful response text
        const botMsgRaw = data.error ? `🚨 Error: ${data.error}` : data.response;
        
        // Parse Markdown to HTML using the 'marked' library (loaded in index.html)
        const botMsgHtml = marked.parse(botMsgRaw);
        chatBox.innerHTML += `<div class="message bot">${botMsgHtml}</div>`;

    } catch (error) {
        console.error('Failed to send message:', error);
        loading.style.display = 'none';
        chatBox.innerHTML += `<div class="message bot">❌ Server connection failed. Please try again later.</div>`;
    } finally {
        // 6. Reset UI State
        sendBtn.disabled = false;
        scrollToBottom();
        inputField.focus(); // Keep focus on input for rapid typing
    }
}

/**
 * Scrolls the chat container to the very bottom.
 * Used to keep the latest message in view.
 */
function scrollToBottom() {
    const chatBox = document.getElementById('chat-box');
    chatBox.scrollTop = chatBox.scrollHeight;
}

/**
 * Escapes HTML characters to prevent Cross-Site Scripting (XSS) attacks.
 * * @param {string} text - The raw text input.
 * @returns {string} - The escaped HTML string.
 */
function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/**
 * Toggles the visibility of the sidebar on mobile devices.
 * Adds/removes the 'active' class to trigger CSS transitions.
 */
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.overlay');
    
    if (sidebar && overlay) {
        sidebar.classList.toggle('active');
        overlay.classList.toggle('active');
    }
}