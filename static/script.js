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

/**
 * -------------------------------------------------------------------------
 * Modal Logic (Contact Developer)
 * -------------------------------------------------------------------------
 */

/**
 * Opens the contact modal with a fade-in animation.
 * Sets display to flex first, then adds the 'show' class for the transition.
 */
function openModal() {
    const modal = document.getElementById('contact-modal');
    modal.style.display = 'flex';
    
    // Slight delay required for the browser to register the display change before animating
    setTimeout(() => {
        modal.classList.add('show');
    }, 10);
}

/**
 * Closes the contact modal.
 * Triggered by clicking the overlay, close button, or confirm button.
 * * @param {Event} event - The click event object.
 */
function closeModal(event) {
    const modal = document.getElementById('contact-modal');
    
    // Close only if clicked on Overlay, Close Button, or Confirm Button
    if (
        event.target === modal || 
        event.target.closest('.close-btn') || 
        event.target.closest('.confirm-btn')
    ) {
        modal.classList.remove('show');
        
        // Wait for the CSS transition (0.3s) to finish before hiding
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300);
    }
}

/**
 * Copies the developer email to the clipboard.
 * Provides visual feedback by temporarily changing the button text and color.
 */
function copyEmail() {
    const emailText = document.getElementById('dev-email').innerText;
    
    navigator.clipboard.writeText(emailText).then(() => {
        const btn = document.querySelector('.copy-btn');
        const originalText = btn.innerText;
        
        // Update button style to indicate success
        btn.innerText = '완료!';
        btn.style.backgroundColor = '#28a745'; // Green
        btn.style.color = '#fff';
        btn.style.borderColor = '#28a745';
        
        // Restore original button state after 1.5 seconds
        setTimeout(() => {
            btn.innerText = originalText;
            btn.style.backgroundColor = '';
            btn.style.color = '';
            btn.style.borderColor = '';
        }, 1500);
    }).catch(err => {
        console.error('Copy failed:', err);
        alert('이메일 복사에 실패했습니다.');
    });
}