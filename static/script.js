/* static/script.js */

async function sendMessage() {
    const inputField = document.getElementById('user-input');
    const message = inputField.value.trim();
    if (!message) return;

    const chatBox = document.getElementById('chat-box');
    const sendBtn = document.getElementById('send-btn');
    const loading = document.getElementById('loading');

    // 1. 사용자 메시지 표시
    chatBox.innerHTML += `<div class="message user">${escapeHtml(message)}</div>`;
    inputField.value = '';
    scrollToBottom();

    // 2. 로딩 시작
    sendBtn.disabled = true;
    chatBox.appendChild(loading);
    loading.style.display = 'block';
    scrollToBottom();

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });
        const data = await response.json();
        
        // 3. 로딩 종료
        loading.style.display = 'none';
        
        // 4. 봇 메시지 (마크다운 파싱)
        const botMsgRaw = data.error ? `🚨 에러: ${data.error}` : data.response;
        
        // marked는 index.html의 CDN에서 로드되므로 전역으로 사용 가능
        const botMsgHtml = marked.parse(botMsgRaw);
        chatBox.innerHTML += `<div class="message bot">${botMsgHtml}</div>`;

    } catch (error) {
        loading.style.display = 'none';
        chatBox.innerHTML += `<div class="message bot">❌ 서버 연결 실패</div>`;
    } finally {
        sendBtn.disabled = false;
        scrollToBottom();
        inputField.focus();
    }
}

function scrollToBottom() {
    const chatBox = document.getElementById('chat-box');
    chatBox.scrollTop = chatBox.scrollHeight;
}

function escapeHtml(text) {
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}