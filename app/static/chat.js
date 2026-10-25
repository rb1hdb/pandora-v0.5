const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('chat-input');
const sendBtn = document.getElementById('btn-send');
const clearBtn = document.getElementById('btn-clear');

const HISTORY_KEY = 'pandora_chat_history';

let history = JSON.parse(sessionStorage.getItem(HISTORY_KEY) || '[]');

function renderMd(text) {
    try {
        const html = typeof marked.parse === 'function' ? marked.parse(text) : marked(text);
        return typeof DOMPurify !== 'undefined' ? DOMPurify.sanitize(html) : html;
    } catch (e) {
        const el = document.createElement('span');
        el.textContent = text;
        return el.innerHTML;
    }
}

function appendMsg(role, text) {
    const wrap = document.createElement('div');
    wrap.className = `msg ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'msg-avatar';
    avatar.textContent = role === 'user' ? '👤' : '🧙';

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    if (role === 'user') {
        bubble.textContent = text;
    } else {
        bubble.innerHTML = renderMd(text);
    }

    wrap.appendChild(avatar);
    wrap.appendChild(bubble);
    messagesEl.appendChild(wrap);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return bubble;
}

function setLoading(on) {
    sendBtn.disabled = on;
    inputEl.disabled = on;
}

function saveHistory() {
    sessionStorage.setItem(HISTORY_KEY, JSON.stringify(history));
}

function restoreMessages() {
    appendMsg('sage', t('chat.welcome'));
    for (const msg of history) {
        appendMsg(msg.role === 'user' ? 'user' : 'sage', msg.content);
    }
}

async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text) return;

    inputEl.value = '';
    inputEl.style.height = 'auto';

    appendMsg('user', text);

    const thinkingBubble = appendMsg('sage', '...');
    thinkingBubble.classList.add('thinking');

    setLoading(true);

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, history }),
        });
        const data = await res.json();
        const reply = data.response || t('chat.no_response');

        thinkingBubble.innerHTML = renderMd(reply);
        thinkingBubble.classList.remove('thinking');

        history.push({ role: 'user', content: text });
        history.push({ role: 'assistant', content: reply });
        saveHistory();
    } catch (e) {
        thinkingBubble.textContent = t('chat.error');
        thinkingBubble.classList.remove('thinking');
    } finally {
        setLoading(false);
        inputEl.focus();
    }
}

sendBtn.addEventListener('click', sendMessage);

inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

inputEl.addEventListener('input', () => {
    inputEl.style.height = 'auto';
    inputEl.style.height = Math.min(inputEl.scrollHeight, 160) + 'px';
});

clearBtn.addEventListener('click', () => {
    history = [];
    sessionStorage.removeItem(HISTORY_KEY);
    messagesEl.innerHTML = '';
    appendMsg('sage', t('chat.welcome'));
});

if (window._i18nReady) {
    restoreMessages();
} else {
    window.addEventListener('i18n-ready', restoreMessages, { once: true });
}

window.addEventListener('i18n-ready', function () {
    const first = messagesEl.querySelector('.msg.sage .msg-bubble');
    if (first) first.innerHTML = renderMd(t('chat.welcome'));
});
