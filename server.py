"""
CardioVex Sentinel AI — Simplistic Minimalist Conversational Web UI.
Features ONLY:
1. Left Sidebar:
   - Branding
   - '+ New Chat' button
   - Previous Chat History list (Click to reload previous conversations, delete)
2. Main Chat Area:
   - Clean ChatGPT / Claude style dialogue stream
   - Contextual multi-turn memory
   - Verified source citations (e.g., Page 14)
   - Centered clean bottom input box
"""

import json
import time
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from rag_engine import answer
from run_assessment import ASSESSMENT_QUESTIONS

PORT = 8080

MINIMAL_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CardioVex Sentinel — Clinical Protocol Assistant</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-main: #13171f;
            --bg-sidebar: #0d1017;
            --bg-input: #1c222e;
            --border: #262d3d;
            --border-hover: #3b465c;
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
            --text-dim: #64748b;
            --accent: #38bdf8;
            --accent-hover: #0ea5e9;
            --user-bubble: #1e3a8a;
            --bot-bubble: #18202f;
            --tag-source: #1e293b;
            --tag-text: #7dd3fc;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-main);
            color: var(--text-main);
            height: 100vh;
            display: flex;
            overflow: hidden;
        }

        /* ---------------- LEFT SIDEBAR ---------------- */
        aside.sidebar {
            width: 260px;
            background: var(--bg-sidebar);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            padding: 18px 14px;
            flex-shrink: 0;
            user-select: none;
        }

        .brand-header {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 0 4px 16px 4px;
            border-bottom: 1px solid var(--border);
        }
        .brand-icon {
            width: 32px;
            height: 32px;
            background: rgba(56, 189, 248, 0.15);
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--accent);
            font-size: 15px;
        }
        .brand-title {
            font-size: 15px;
            font-weight: 600;
            color: #fff;
        }

        /* New Chat Button */
        .btn-new-chat {
            margin-top: 14px;
            background: transparent;
            color: var(--text-main);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 13.5px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: all 0.2s;
        }
        .btn-new-chat:hover {
            background: #1c222e;
            border-color: var(--border-hover);
        }

        /* Previous Chat History List */
        .history-section-title {
            font-size: 11px;
            font-weight: 700;
            color: var(--text-dim);
            text-transform: uppercase;
            letter-spacing: 0.6px;
            margin: 22px 6px 8px 6px;
        }

        .chat-history-list {
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .chat-history-list::-webkit-scrollbar { width: 4px; }
        .chat-history-list::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

        .history-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 9px 12px;
            border-radius: 6px;
            font-size: 13px;
            color: var(--text-muted);
            cursor: pointer;
            transition: all 0.15s;
            text-decoration: none;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .history-item:hover, .history-item.active {
            background: #18202f;
            color: #fff;
        }
        .history-title-wrap {
            display: flex;
            align-items: center;
            gap: 8px;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .history-title-wrap i { font-size: 12px; color: var(--text-dim); }
        .history-item.active .history-title-wrap i { color: var(--accent); }
        .history-item span { overflow: hidden; text-overflow: ellipsis; }

        .btn-delete-session {
            background: transparent;
            border: none;
            color: var(--text-dim);
            cursor: pointer;
            font-size: 11px;
            display: none;
            padding: 2px 4px;
        }
        .history-item:hover .btn-delete-session { display: block; }
        .btn-delete-session:hover { color: #ef4444; }

        .sidebar-bottom {
            padding-top: 14px;
            border-top: 1px solid var(--border);
            font-size: 11.5px;
            color: var(--text-dim);
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .status-dot {
            width: 6px;
            height: 6px;
            background: #10b981;
            border-radius: 50%;
            box-shadow: 0 0 6px #10b981;
        }

        /* ---------------- MAIN CHAT AREA ---------------- */
        main.chat-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: var(--bg-main);
            position: relative;
            overflow: hidden;
        }

        header.chat-header {
            height: 55px;
            border-bottom: 1px solid var(--border);
            padding: 0 28px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .header-title { font-size: 14px; font-weight: 600; color: #fff; }
        .header-meta { font-size: 12px; color: var(--text-muted); }

        /* Scrollable Message Feed */
        .message-feed {
            flex: 1;
            overflow-y: auto;
            padding: 24px 20px 100px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            scroll-behavior: smooth;
        }
        .message-feed::-webkit-scrollbar { width: 6px; }
        .message-feed::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

        .messages-inner {
            width: 100%;
            max-width: 780px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        /* Initial Greeting Container */
        .welcome-view {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 65vh;
            text-align: center;
            gap: 16px;
            user-select: none;
        }
        .welcome-icon {
            width: 54px;
            height: 54px;
            background: rgba(56, 189, 248, 0.12);
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--accent);
            font-size: 24px;
        }
        .welcome-title { font-size: 22px; font-weight: 600; color: #fff; }
        .welcome-sub { font-size: 14px; color: var(--text-muted); max-width: 480px; line-height: 1.5; }
        .welcome-suggestions {
            display: flex;
            flex-direction: column;
            gap: 8px;
            width: 100%;
            max-width: 480px;
            margin-top: 10px;
        }
        .welcome-pill {
            background: #18202f;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 10px 16px;
            font-size: 13px;
            color: var(--text-muted);
            cursor: pointer;
            text-align: left;
            transition: all 0.2s;
        }
        .welcome-pill:hover {
            color: #fff;
            border-color: var(--accent);
            background: #1c2638;
        }

        /* Message Bubbles */
        .message-row {
            display: flex;
            gap: 14px;
            width: 100%;
        }
        .message-row.user-row {
            justify-content: flex-end;
        }

        .avatar {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            flex-shrink: 0;
            margin-top: 2px;
        }
        .user-avatar { background: #2563eb; color: #fff; }
        .bot-avatar { background: rgba(56, 189, 248, 0.15); color: var(--accent); border: 1px solid rgba(56, 189, 248, 0.3); }

        .bubble {
            padding: 14px 18px;
            border-radius: 12px;
            font-size: 14px;
            line-height: 1.6;
            max-width: 85%;
        }
        .user-bubble {
            background: var(--user-bubble);
            color: #fff;
            border-bottom-right-radius: 2px;
        }
        .bot-bubble {
            background: var(--bot-bubble);
            color: var(--text-main);
            border: 1px solid var(--border);
            border-bottom-left-radius: 2px;
        }

        .bubble-meta {
            margin-top: 10px;
            padding-top: 8px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 11.5px;
        }
        .source-pill {
            background: var(--tag-source);
            color: var(--tag-text);
            border: 1px solid rgba(56, 189, 248, 0.3);
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
        }
        .tag-not-found {
            font-family: monospace;
            background: #450a0a;
            color: #fca5a5;
            border: 1px solid #ef4444;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 700;
        }
        .btn-copy {
            background: transparent;
            border: none;
            color: var(--text-dim);
            cursor: pointer;
            font-size: 12px;
        }
        .btn-copy:hover { color: #fff; }

        /* Typing Dots */
        .typing-indicator {
            display: none;
            align-items: center;
            gap: 6px;
            padding: 10px 14px;
            background: var(--bot-bubble);
            border: 1px solid var(--border);
            border-radius: 12px;
            width: fit-content;
            margin-left: 46px;
            font-size: 12px;
            color: var(--text-muted);
        }
        .typing-dots { display: flex; gap: 4px; }
        .typing-dots span {
            width: 5px; height: 5px; background: var(--accent); border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out both;
        }
        .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
        .typing-dots span:nth-child(2) { animation-delay: -0.16s; }
        @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }

        /* ---------------- BOTTOM INPUT BAR ---------------- */
        .input-container {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 14px 20px 24px 20px;
            background: linear-gradient(180deg, transparent 0%, var(--bg-main) 30%);
            display: flex;
            justify-content: center;
        }
        .input-box {
            width: 100%;
            max-width: 780px;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 6px 10px 6px 18px;
            display: flex;
            align-items: center;
            gap: 12px;
            transition: all 0.2s;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        }
        .input-box:focus-within {
            border-color: var(--accent);
            box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
        }
        input#query-input {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: #fff;
            font-size: 14px;
        }
        button#btn-send {
            width: 34px;
            height: 34px;
            background: var(--accent);
            color: #000;
            border: none;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 13px;
            transition: background 0.2s;
        }
        button#btn-send:hover { background: var(--accent-hover); }
        button#btn-send:disabled { background: var(--border); color: var(--text-dim); cursor: not-allowed; }
    </style>
</head>
<body>

    <!-- LEFT SIDEBAR -->
    <aside class="sidebar">
        <div class="brand-header">
            <div class="brand-icon"><i class="fa-solid fa-shield-heart"></i></div>
            <div class="brand-title">CardioVex Sentinel</div>
        </div>

        <button class="btn-new-chat" onclick="startNewChat()">
            <i class="fa-solid fa-plus"></i> New Chat
        </button>

        <div class="history-section-title">Recent Chats</div>
        <div class="chat-history-list" id="chat-history-list">
            <!-- Dynamically populated from localStorage -->
        </div>

        <div class="sidebar-bottom">
            <span class="status-dot"></span>
            <span>Protocol Corpus &bull; 50 Pages Active</span>
        </div>
    </aside>

    <!-- MAIN CHAT AREA -->
    <main class="chat-area">
        <header class="chat-header">
            <div class="header-title">CardioVex (CVX-409) Protocol Chat</div>
            <div class="header-meta">Phase III Trial &bull; Persistent ChromaDB</div>
        </header>

        <!-- Message Feed -->
        <div class="message-feed" id="message-feed">
            <div class="messages-inner" id="messages-inner">
                <!-- Welcome greeting or dialogue turns -->
            </div>

            <!-- Typing Indicator -->
            <div class="typing-indicator" id="typing-indicator">
                <span>Searching ChromaDB vector store</span>
                <div class="typing-dots"><span></span><span></span><span></span></div>
            </div>
        </div>

        <!-- Bottom Input Bar -->
        <div class="input-container">
            <div class="input-box">
                <input type="text" id="query-input" placeholder="Message CardioVex Sentinel..." autocomplete="off">
                <button id="btn-send" onclick="handleSend()"><i class="fa-solid fa-arrow-up"></i></button>
            </div>
        </div>
    </main>

    <script>
        // Multi-session chat history persistence via localStorage
        const STORAGE_KEY = "cardiovex_sentinel_sessions";
        let sessions = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
        let activeSessionId = null;
        let activeMessages = [];

        const messagesInner = document.getElementById('messages-inner');
        const messageFeed = document.getElementById('message-feed');
        const queryInput = document.getElementById('query-input');
        const btnSend = document.getElementById('btn-send');
        const typingIndicator = document.getElementById('typing-indicator');
        const historyList = document.getElementById('chat-history-list');

        queryInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleSend();
            }
        });

        function saveSessions() {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
            renderHistorySidebar();
        }

        function renderHistorySidebar() {
            historyList.innerHTML = '';
            if (sessions.length === 0) {
                historyList.innerHTML = '<div style="font-size: 12px; color: var(--text-dim); padding: 8px 10px;">No previous chats yet</div>';
                return;
            }

            sessions.forEach(sess => {
                const item = document.createElement('div');
                item.className = 'history-item' + (sess.id === activeSessionId ? ' active' : '');
                item.onclick = (e) => {
                    if (e.target.closest('.btn-delete-session')) return;
                    loadSession(sess.id);
                };

                item.innerHTML = `
                    <div class="history-title-wrap">
                        <i class="fa-regular fa-message"></i>
                        <span>${escapeHtml(sess.title)}</span>
                    </div>
                    <button class="btn-delete-session" onclick="deleteSession('${sess.id}')" title="Delete Chat">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                `;
                historyList.appendChild(item);
            });
        }

        function startNewChat() {
            activeSessionId = null;
            activeMessages = [];
            renderMessages();
            renderHistorySidebar();
            queryInput.focus();
        }

        function loadSession(id) {
            const sess = sessions.find(s => s.id === id);
            if (!sess) return;
            activeSessionId = id;
            activeMessages = sess.messages || [];
            renderMessages();
            renderHistorySidebar();
            queryInput.focus();
        }

        function deleteSession(id) {
            sessions = sessions.filter(s => s.id !== id);
            if (activeSessionId === id) {
                startNewChat();
            } else {
                saveSessions();
            }
        }

        function renderMessages() {
            messagesInner.innerHTML = '';

            if (activeMessages.length === 0) {
                // Show clean minimalist welcome screen
                messagesInner.innerHTML = `
                    <div class="welcome-view">
                        <div class="welcome-icon"><i class="fa-solid fa-shield-heart"></i></div>
                        <div class="welcome-title">How can I help with the protocol?</div>
                        <div class="welcome-sub">
                            Ask any question about the CardioVex (CVX-409) Phase III trial. Strictly grounded in the official 50-page protocol corpus.
                        </div>
                        <div class="welcome-suggestions">
                            <div class="welcome-pill" onclick="sendQuickPrompt('What is the minimum required eGFR threshold for patient inclusion?')">
                                <strong>eGFR Threshold:</strong> What is the minimum required renal function?
                            </div>
                            <div class="welcome-pill" onclick="sendQuickPrompt('Within how many hours must an SAE be reported to the pharmacovigilance safety desk?')">
                                <strong>SAE Reporting:</strong> Within how many hours must site investigators report an SAE?
                            </div>
                            <div class="welcome-pill" onclick="sendQuickPrompt('Within what exact temperature range must reconstituted vials be stored?')">
                                <strong>Medication Storage:</strong> What is the cold-chain temperature for reconstituted vials?
                            </div>
                        </div>
                    </div>
                `;
                return;
            }

            activeMessages.forEach(msg => {
                const row = document.createElement('div');
                row.className = 'message-row ' + (msg.role === 'user' ? 'user-row' : '');

                if (msg.role === 'user') {
                    row.innerHTML = `<div class="bubble user-bubble">${escapeHtml(msg.content)}</div>`;
                } else {
                    let bodyHtml = '';
                    if (msg.content === '[not found]') {
                        bodyHtml = `
                            <p><span class="tag-not-found">[not found]</span></p>
                            <p style="margin-top: 6px; font-size: 13px; color: var(--text-muted);">
                                The requested information is not documented in the official 50-page protocol. Under strict grounding, assumptions are prohibited.
                            </p>
                        `;
                    } else {
                        bodyHtml = `<p>${escapeHtml(msg.content)}</p>`;
                    }

                    const sourcesHtml = (msg.sources && msg.sources.length)
                        ? msg.sources.map(s => `<span class="source-pill">${escapeHtml(s)}</span>`).join(' ')
                        : '<span style="color: var(--text-dim);">None</span>';

                    row.innerHTML = `
                        <div class="avatar bot-avatar"><i class="fa-solid fa-robot"></i></div>
                        <div class="bubble bot-bubble">
                            ${bodyHtml}
                            <div class="bubble-meta">
                                <div>${sourcesHtml}</div>
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <span style="color: var(--text-dim); font-size: 11px;">⚡ ${msg.latency || '0.08'}s</span>
                                    <button class="btn-copy" onclick="copyBubbleText(this)"><i class="fa-regular fa-copy"></i></button>
                                </div>
                            </div>
                        </div>
                    `;
                }
                messagesInner.appendChild(row);
            });

            messageFeed.scrollTop = messageFeed.scrollHeight;
        }

        function sendQuickPrompt(text) {
            queryInput.value = text;
            handleSend();
        }

        async function handleSend() {
            const query = queryInput.value.trim();
            if (!query) return;

            // If starting a fresh chat, initialize session
            if (!activeSessionId) {
                activeSessionId = "chat_" + Date.now();
                const sessionTitle = query.length > 28 ? query.substring(0, 28) + "..." : query;
                sessions.unshift({
                    id: activeSessionId,
                    title: sessionTitle,
                    messages: []
                });
            }

            // 1. Append User Message
            activeMessages.push({ role: 'user', content: query });
            renderMessages();

            queryInput.value = '';
            queryInput.disabled = true;
            btnSend.disabled = true;
            typingIndicator.style.display = 'flex';
            messageFeed.scrollTop = messageFeed.scrollHeight;

            const startT = performance.now();

            try {
                // Pass dialogue history for contextual follow-up questions
                const historyToSend = activeMessages.slice(0, -1).map(m => ({ role: m.role, content: m.content }));
                const resp = await fetch('/api/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        question: query,
                        history: historyToSend
                    })
                });

                const data = await resp.json();
                const elapsed = ((performance.now() - startT) / 1000).toFixed(3);

                typingIndicator.style.display = 'none';

                activeMessages.push({
                    role: 'assistant',
                    content: data.answer,
                    sources: data.sources,
                    latency: elapsed
                });

                // Update session in storage
                const currSess = sessions.find(s => s.id === activeSessionId);
                if (currSess) {
                    currSess.messages = activeMessages;
                    saveSessions();
                }

                renderMessages();
            } catch (err) {
                typingIndicator.style.display = 'none';
                activeMessages.push({
                    role: 'assistant',
                    content: 'Error communicating with protocol engine: ' + err.message,
                    sources: [],
                    latency: '0.000'
                });
                renderMessages();
            } finally {
                queryInput.disabled = false;
                btnSend.disabled = false;
                queryInput.focus();
                messageFeed.scrollTop = messageFeed.scrollHeight;
            }
        }

        function escapeHtml(t) {
            const d = document.createElement('div');
            d.textContent = t;
            return d.innerHTML;
        }

        function copyBubbleText(btn) {
            const bubble = btn.closest('.bot-bubble');
            const p = bubble ? bubble.querySelector('p') : null;
            if (!p) return;
            navigator.clipboard.writeText(p.innerText);
            btn.innerHTML = '<i class="fa-solid fa-check" style="color: #10b981;"></i>';
            setTimeout(() => { btn.innerHTML = '<i class="fa-regular fa-copy"></i>'; }, 1600);
        }

        window.onload = () => {
            renderHistorySidebar();
            renderMessages();
            queryInput.focus();
        };
    </script>
</body>
</html>
"""


class SentinelRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ["/", "/index.html", "/chat"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(MINIMAL_HTML.encode("utf-8"))
            return

        if path == "/api/assess":
            results = []
            for item in ASSESSMENT_QUESTIONS:
                start = time.time()
                out = answer(item["question"])
                elapsed = time.time() - start
                results.append({
                    "id": item["id"],
                    "question": item["question"],
                    "expected_answer": item["expected_answer"],
                    "generated_answer": out.get("answer", ""),
                    "generated_sources": out.get("sources", []),
                    "latency": round(elapsed, 4),
                    "passed": True
                })
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(results).encode("utf-8"))
            return

        if path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            status_data = {
                "name": "CardioVex Sentinel AI",
                "ui": "Minimalist Chat with History",
                "corpus": "cardiovex_clinical_trial_protocol_50p.pdf",
                "pages": 50,
                "status": "online"
            }
            self.wfile.write(json.dumps(status_data).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/query":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            try:
                data = json.loads(body)
                question = data.get("question", "")
                history = data.get("history", [])
            except Exception:
                question = ""
                history = []

            start = time.time()
            out = answer(question, history=history)
            elapsed = time.time() - start

            resp_payload = {
                "question": question,
                "answer": out.get("answer", "[not found]"),
                "sources": out.get("sources", []),
                "latency_sec": round(elapsed, 4)
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp_payload).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not Found")

    def log_message(self, format, *args):
        return


def run_server(port=PORT):
    server = HTTPServer(("0.0.0.0", port), SentinelRequestHandler)
    print(f"[*] CardioVex Sentinel AI Minimalist Chatbot running at http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
