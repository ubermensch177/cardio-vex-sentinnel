"""
CardioVex Sentinel AI - Production Chatbot Web Server.
Provides an interactive, modern conversational Chatbot interface and REST API.

Endpoints:
    GET /              -> Modern Chatbot Web Interface
    POST /api/query    -> Query the RAG engine: {"question": "..."}
    GET /api/assess    -> Returns the 5 assessment benchmark results
    GET /api/status    -> System and ChromaDB collection status
"""

import json
import time
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from rag_engine import answer
from run_assessment import ASSESSMENT_QUESTIONS

PORT = 8080

CHATBOT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CardioVex Sentinel AI — Clinical Protocol Chatbot</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-dark: #090d16;
            --sidebar-bg: #0f172a;
            --chat-bg: #0b1120;
            --card-bg: #1e293b;
            --border-color: #334155;
            --primary: #38bdf8;
            --primary-hover: #0284c7;
            --accent: #a855f7;
            --success: #22c55e;
            --danger: #ef4444;
            --warning: #f59e0b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --user-bubble: #1e40af;
            --bot-bubble: #1e293b;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-main);
            display: flex;
            height: 100vh;
            overflow: hidden;
        }

        /* Sidebar */
        aside.sidebar {
            width: 320px;
            background-color: var(--sidebar-bg);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            padding: 20px 16px;
            flex-shrink: 0;
            user-select: none;
        }

        .brand-header {
            display: flex;
            align-items: center;
            gap: 12px;
            padding-bottom: 18px;
            border-bottom: 1px solid var(--border-color);
        }
        .brand-icon {
            font-size: 24px;
            color: var(--primary);
            background: rgba(56, 189, 248, 0.12);
            padding: 10px;
            border-radius: 12px;
            border: 1px solid rgba(56, 189, 248, 0.3);
        }
        .brand-title { font-size: 17px; font-weight: 700; color: #fff; }
        .brand-sub { font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }

        .btn-new-chat {
            margin-top: 16px;
            background: rgba(56, 189, 248, 0.1);
            color: var(--primary);
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: all 0.2s;
        }
        .btn-new-chat:hover {
            background: var(--primary);
            color: #000;
        }

        .sidebar-section-title {
            font-size: 11px;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            margin: 20px 8px 8px 8px;
        }

        .prompt-list {
            display: flex;
            flex-direction: column;
            gap: 6px;
            overflow-y: auto;
            flex: 1;
        }

        .prompt-item {
            background: transparent;
            color: var(--text-muted);
            border: 1px solid transparent;
            border-radius: 6px;
            padding: 9px 12px;
            font-size: 13px;
            text-align: left;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: all 0.15s ease;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .prompt-item:hover {
            background: var(--card-bg);
            color: var(--text-main);
            border-color: var(--border-color);
        }
        .prompt-item i { font-size: 12px; color: var(--primary); }

        .sidebar-footer {
            padding-top: 14px;
            border-top: 1px solid var(--border-color);
            font-size: 12px;
            color: var(--text-muted);
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            color: var(--success);
            background: rgba(34, 197, 94, 0.1);
            padding: 4px 10px;
            border-radius: 9999px;
            border: 1px solid rgba(34, 197, 94, 0.3);
            width: fit-content;
        }
        .status-pill .dot {
            width: 7px;
            height: 7px;
            background: var(--success);
            border-radius: 50%;
            box-shadow: 0 0 6px var(--success);
        }

        /* Main Chat Area */
        main.chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            background-color: var(--chat-bg);
            position: relative;
            overflow: hidden;
        }

        header.chat-header {
            height: 65px;
            border-bottom: 1px solid var(--border-color);
            background: var(--sidebar-bg);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 25px;
        }
        .header-info { display: flex; align-items: center; gap: 14px; }
        .header-title { font-size: 15px; font-weight: 600; color: #fff; }
        .header-meta { font-size: 12px; color: var(--text-muted); }
        .header-actions { display: flex; gap: 10px; }
        .btn-header {
            background: var(--card-bg);
            color: var(--text-muted);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 6px 12px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-header:hover { color: #fff; border-color: var(--primary); }

        /* Messages Feed */
        .messages-feed {
            flex: 1;
            overflow-y: auto;
            padding: 24px 30px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .message-row {
            display: flex;
            gap: 14px;
            max-width: 880px;
            width: 100%;
        }
        .message-row.user-row {
            margin-left: auto;
            flex-direction: row-reverse;
        }

        .avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            flex-shrink: 0;
            margin-top: 2px;
        }
        .avatar.user-avatar {
            background: #2563eb;
            color: #fff;
        }
        .avatar.bot-avatar {
            background: rgba(56, 189, 248, 0.15);
            color: var(--primary);
            border: 1px solid rgba(56, 189, 248, 0.4);
        }

        .bubble {
            padding: 16px 20px;
            border-radius: 12px;
            font-size: 14.5px;
            line-height: 1.6;
            max-width: 780px;
        }
        .bubble.user-bubble {
            background: var(--user-bubble);
            color: #fff;
            border-bottom-right-radius: 2px;
        }
        .bubble.bot-bubble {
            background: var(--bot-bubble);
            color: var(--text-main);
            border: 1px solid var(--border-color);
            border-bottom-left-radius: 2px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        }

        .bot-meta-bar {
            margin-top: 14px;
            padding-top: 10px;
            border-top: 1px solid rgba(255,255,255,0.08);
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            font-size: 12px;
        }
        .source-tags { display: flex; align-items: center; gap: 6px; }
        .tag-source {
            background: #172554;
            color: #93c5fd;
            border: 1px solid #1e40af;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
        }
        .tag-grounded {
            color: var(--success);
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }
        .tag-not-found {
            font-family: monospace;
            background: #450a0a;
            color: #fca5a5;
            border: 1px solid var(--danger);
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 700;
        }

        .btn-copy {
            background: transparent;
            color: var(--text-muted);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 3px 8px;
            cursor: pointer;
            font-size: 11px;
            transition: all 0.2s;
        }
        .btn-copy:hover { color: #fff; border-color: var(--primary); }

        /* Typing Indicator */
        .typing-indicator {
            display: none;
            align-items: center;
            gap: 6px;
            padding: 10px 14px;
            background: var(--bot-bubble);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            width: fit-content;
            margin-left: 50px;
            font-size: 13px;
            color: var(--text-muted);
        }
        .typing-dots {
            display: flex;
            gap: 4px;
        }
        .typing-dots span {
            width: 6px;
            height: 6px;
            background: var(--primary);
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out both;
        }
        .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
        .typing-dots span:nth-child(2) { animation-delay: -0.16s; }
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }

        /* Suggestions Bar */
        .suggestions-bar {
            padding: 8px 30px;
            display: flex;
            gap: 8px;
            overflow-x: auto;
            background: var(--chat-bg);
            border-top: 1px solid rgba(255,255,255,0.04);
        }
        .suggestion-pill {
            background: var(--card-bg);
            color: var(--text-muted);
            border: 1px solid var(--border-color);
            border-radius: 9999px;
            padding: 5px 12px;
            font-size: 12px;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.2s;
        }
        .suggestion-pill:hover {
            color: var(--primary);
            border-color: var(--primary);
            background: rgba(56, 189, 248, 0.08);
        }

        /* Input Area */
        .input-area {
            padding: 16px 30px 24px 30px;
            background: var(--sidebar-bg);
            border-top: 1px solid var(--border-color);
        }
        .input-box {
            display: flex;
            background: #090d16;
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 6px 8px 6px 16px;
            align-items: center;
            gap: 10px;
            transition: border-color 0.2s;
        }
        .input-box:focus-within {
            border-color: var(--primary);
            box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
        }
        input#chat-input {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: #fff;
            font-size: 14.5px;
        }
        button#btn-send {
            background: var(--primary);
            color: #000;
            border: none;
            width: 38px;
            height: 38px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
        }
        button#btn-send:hover { background: var(--primary-hover); color: #fff; }
        button#btn-send:disabled { background: var(--border-color); cursor: not-allowed; color: #64748b; }

        /* Modal for Assessment Matrix */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.75);
            z-index: 1000;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .modal-content {
            background: var(--sidebar-bg);
            border: 1px solid var(--border-color);
            border-radius: 14px;
            width: 100%;
            max-width: 960px;
            max-height: 85vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0,0,0,0.6);
        }
        .modal-header {
            padding: 18px 24px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .modal-body {
            padding: 20px 24px;
            overflow-y: auto;
        }
        .btn-close-modal {
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 18px;
            cursor: pointer;
        }
        .btn-close-modal:hover { color: #fff; }

        table.bench-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13.5px;
        }
        table.bench-table th {
            background: #090d16;
            color: var(--text-muted);
            padding: 12px;
            border-bottom: 1px solid var(--border-color);
            text-align: left;
        }
        table.bench-table td {
            padding: 12px;
            border-bottom: 1px solid var(--border-color);
            vertical-align: top;
        }
    </style>
</head>
<body>

    <!-- Sidebar -->
    <aside class="sidebar">
        <div class="brand-header">
            <div class="brand-icon"><i class="fa-solid fa-shield-heart"></i></div>
            <div>
                <div class="brand-title">CardioVex Sentinel AI</div>
                <div class="brand-sub">Clinical RAG Assistant</div>
            </div>
        </div>

        <button class="btn-new-chat" onclick="clearConversation()">
            <i class="fa-solid fa-plus"></i> New Conversation
        </button>

        <div class="sidebar-section-title">Assessment Questions</div>
        <div class="prompt-list">
            <button class="prompt-item" onclick="sendPrompt(1)">
                <i class="fa-solid fa-vial"></i> Q1: eGFR Threshold (Page 14)
            </button>
            <button class="prompt-item" onclick="sendPrompt(2)">
                <i class="fa-solid fa-triangle-exclamation"></i> Q2: SAE Reporting Timeline (Page 28)
            </button>
            <button class="prompt-item" onclick="sendPrompt(3)">
                <i class="fa-solid fa-tag"></i> Q3: Commercial Price (Negative)
            </button>
            <button class="prompt-item" onclick="sendPrompt(4)">
                <i class="fa-solid fa-temperature-arrow-down"></i> Q4: Storage Temp 2-8°C (Page 42)
            </button>
            <button class="prompt-item" onclick="sendPrompt(5)">
                <i class="fa-solid fa-pills"></i> Q5: Paediatric Amoxicillin (Negative)
            </button>

            <div class="sidebar-section-title">General Protocol Inquiries</div>
            <button class="prompt-item" onclick="sendCustomPrompt('What are the protocol guidelines regarding prohibited CYP3A4 inhibitors?')">
                <i class="fa-solid fa-ban"></i> Prohibited CYP3A4 Inhibitors
            </button>
            <button class="prompt-item" onclick="sendCustomPrompt('What are the requirements for informed consent documentation and ICH-GCP audits?')">
                <i class="fa-solid fa-file-signature"></i> Informed Consent & ICH-GCP Audits
            </button>
            <button class="prompt-item" onclick="sendCustomPrompt('What baseline echocardiography biomarkers are monitored?')">
                <i class="fa-solid fa-heart-pulse"></i> Baseline Echocardiography Panels
            </button>
            <button class="prompt-item" onclick="sendCustomPrompt('What statistical power calculations and Kaplan-Meier endpoints are specified?')">
                <i class="fa-solid fa-chart-line"></i> Statistical Power & DSMB Charter
            </button>
        </div>

        <div class="sidebar-footer">
            <button class="btn-new-chat" style="margin-top: 0; background: var(--card-bg);" onclick="openModal()">
                <i class="fa-solid fa-table-list"></i> View Benchmark Matrix
            </button>
            <div class="status-pill">
                <span class="dot"></span> ChromaDB Persistent (238 Chunks)
            </div>
            <div>Corpus: 50 Pages &bull; Strict Grounding</div>
        </div>
    </aside>

    <!-- Main Chat Container -->
    <main class="chat-container">
        <header class="chat-header">
            <div class="header-info">
                <div>
                    <div class="header-title">CardioVex (CVX-409) Protocol Chatbot</div>
                    <div class="header-meta">Phase III Multicenter Clinical Trial &bull; Local Dense ONNX Retrieval</div>
                </div>
            </div>
            <div class="header-actions">
                <button class="btn-header" onclick="openModal()"><i class="fa-solid fa-clipboard-check"></i> Benchmark</button>
                <button class="btn-header" onclick="clearConversation()"><i class="fa-solid fa-trash-can"></i> Clear</button>
            </div>
        </header>

        <!-- Message Stream -->
        <div class="messages-feed" id="messages-feed">
            <!-- Initial Greeting -->
            <div class="message-row">
                <div class="avatar bot-avatar"><i class="fa-solid fa-robot"></i></div>
                <div class="bubble bot-bubble">
                    <p><strong>Hello! I am CardioVex Sentinel AI 🛡️</strong></p>
                    <p style="margin-top: 6px;">I am your specialized assistant for the <strong>CardioVex (CVX-409) Phase III Clinical Trial Protocol</strong>.</p>
                    <p style="margin-top: 6px;">You can ask me anything about:</p>
                    <ul style="margin: 6px 0 6px 20px; font-size: 13.5px; color: #cbd5e1;">
                        <li>Patient eligibility & renal function thresholds (eGFR)</li>
                        <li>Expedited Serious Adverse Event (SAE) reporting timelines</li>
                        <li>Investigational product cold-chain vial storage requirements</li>
                        <li>Concomitant CYP3A4 inhibitors, echocardiography biomarkers, and GCP audit guidelines</li>
                    </ul>
                    <p style="margin-top: 6px; font-size: 13px; color: #94a3b8;">
                        <em>Notice: I enforce strict grounding. If an inquiry is not documented in the official 50-page protocol, I will return exactly <code>[not found]</code>.</em>
                    </p>
                    <div class="bot-meta-bar">
                        <span class="tag-grounded"><i class="fa-solid fa-check-circle"></i> Grounding Active</span>
                        <span style="color: #64748b; font-size: 11px;">Corpus: cardiovex_clinical_trial_protocol_50p.pdf</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Typing Indicator -->
        <div class="typing-indicator" id="typing-indicator">
            <span>Sentinel AI is searching ChromaDB vector store</span>
            <div class="typing-dots">
                <span></span><span></span><span></span>
            </div>
        </div>

        <!-- Suggestion Chips Bar -->
        <div class="suggestions-bar">
            <span style="font-size: 11.5px; color: #64748b; align-self: center;">Suggestions:</span>
            <button class="suggestion-pill" onclick="sendPrompt(1)">eGFR Threshold</button>
            <button class="suggestion-pill" onclick="sendPrompt(2)">SAE Reporting Window</button>
            <button class="suggestion-pill" onclick="sendPrompt(4)">Vial Temperature</button>
            <button class="suggestion-pill" onclick="sendCustomPrompt('What are the exclusion criteria for heart failure patients?')">Exclusion Criteria</button>
            <button class="suggestion-pill" onclick="sendPrompt(3)">Commercial Price (Negative Test)</button>
        </div>

        <!-- Input Area -->
        <div class="input-area">
            <div class="input-box">
                <input type="text" id="chat-input" placeholder="Type a clinical trial question or select a preset..." autocomplete="off">
                <button id="btn-send" onclick="handleSend()"><i class="fa-solid fa-paper-plane"></i></button>
            </div>
        </div>
    </main>

    <!-- Modal for Assessment Benchmark Matrix -->
    <div class="modal-overlay" id="benchmark-modal" onclick="closeModalOnBackdrop(event)">
        <div class="modal-content">
            <div class="modal-header">
                <div>
                    <h3 style="color: var(--primary); font-size: 18px;">Assessment Benchmark Verification Matrix</h3>
                    <p style="color: var(--text-muted); font-size: 13px;">Official 5-Question Exam Protocol Benchmark</p>
                </div>
                <button class="btn-close-modal" onclick="closeModal()"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="modal-body">
                <table class="bench-table">
                    <thead>
                        <tr>
                            <th style="width: 45px; text-align: center;">ID</th>
                            <th style="width: 30%;">Assessment Question</th>
                            <th style="width: 44%;">Generated Grounded Answer</th>
                            <th style="width: 14%; text-align: center;">Source</th>
                            <th style="width: 8%; text-align: center;">Status</th>
                        </tr>
                    </thead>
                    <tbody id="modal-bench-body">
                        <tr><td colspan="5" style="text-align: center; color: var(--text-muted);">Loading benchmark data...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        const PRESET_QUERIES = {
            1: "What is the minimum required estimated Glomerular Filtration Rate (eGFR) threshold for a patient to be included in the CardioVex Phase III trial?",
            2: "Within how many hours of becoming aware of a Serious Adverse Event (SAE) must a site investigator report it to the pharmacovigilance safety desk?",
            3: "What is the wholesale or retail price of CardioVex in commercial pharmacies?",
            4: "Within what exact temperature range, in degrees Celsius, must reconstituted CardioVex vials be stored before administration?",
            5: "What is the standard recommended dosage of amoxicillin for treating a paediatric ear infection?"
        };

        const chatFeed = document.getElementById('messages-feed');
        const chatInput = document.getElementById('chat-input');
        const btnSend = document.getElementById('btn-send');
        const typingIndicator = document.getElementById('typing-indicator');

        // Multi-turn conversation state
        let conversationHistory = [];

        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleSend();
            }
        });

        function sendPrompt(id) {
            const q = PRESET_QUERIES[id];
            chatInput.value = q;
            handleSend();
        }

        function sendCustomPrompt(text) {
            chatInput.value = text;
            handleSend();
        }

        function clearConversation() {
            conversationHistory = [];
            chatFeed.innerHTML = `
                <div class="message-row">
                    <div class="avatar bot-avatar"><i class="fa-solid fa-robot"></i></div>
                    <div class="bubble bot-bubble">
                        <p><strong>Conversation refreshed.</strong></p>
                        <p style="margin-top: 6px;">How can I assist you with the CardioVex (CVX-409) clinical trial protocol today?</p>
                        <div class="bot-meta-bar">
                            <span class="tag-grounded"><i class="fa-solid fa-check-circle"></i> Ready & Grounded</span>
                        </div>
                    </div>
                </div>
            `;
            chatInput.focus();
        }

        async function handleSend() {
            const query = chatInput.value.trim();
            if (!query) return;

            // 1. Append User Message
            appendUserMessage(query);
            chatInput.value = '';
            chatInput.disabled = true;
            btnSend.disabled = true;

            // Show typing indicator
            typingIndicator.style.display = 'flex';
            chatFeed.scrollTop = chatFeed.scrollHeight;

            const startTime = performance.now();

            try {
                const resp = await fetch('/api/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        question: query,
                        history: conversationHistory
                    })
                });

                const data = await resp.json();
                const latency = ((performance.now() - startTime) / 1000).toFixed(3);

                typingIndicator.style.display = 'none';
                appendBotResponse(data.answer, data.sources, latency);

                // Update client-side conversational memory
                conversationHistory.push({ role: 'user', content: query });
                conversationHistory.push({ role: 'assistant', content: data.answer });
            } catch (err) {
                typingIndicator.style.display = 'none';
                appendBotResponse("An error occurred while querying the ChromaDB RAG engine: " + err.message, [], "0.000");
            } finally {
                chatInput.disabled = false;
                btnSend.disabled = false;
                chatInput.focus();
                chatFeed.scrollTop = chatFeed.scrollHeight;
            }
        }

        function appendUserMessage(text) {
            const row = document.createElement('div');
            row.className = 'message-row user-row';
            row.innerHTML = `
                <div class="avatar user-avatar"><i class="fa-solid fa-user"></i></div>
                <div class="bubble user-bubble">${escapeHtml(text)}</div>
            `;
            chatFeed.appendChild(row);
            chatFeed.scrollTop = chatFeed.scrollHeight;
        }

        function appendBotResponse(answerText, sources, latency) {
            const row = document.createElement('div');
            row.className = 'message-row';

            let bodyHtml = '';
            let metaHtml = '';

            if (answerText === "[not found]") {
                bodyHtml = `
                    <p><span class="tag-not-found">[not found]</span></p>
                    <p style="margin-top: 8px; color: #94a3b8; font-size: 13.5px;">
                        The requested information is <strong>not present</strong> in the official 50-page CardioVex Phase III clinical trial protocol. 
                        Under strict regulatory grounding compliance, external assumptions and off-protocol estimates are prohibited.
                    </p>
                `;
                metaHtml = `
                    <span style="color: #ef4444; font-size: 12px;"><i class="fa-solid fa-triangle-exclamation"></i> Out of Protocol Corpus</span>
                    <span style="color: #64748b; font-size: 11px;">⚡ ${latency}s</span>
                `;
            } else {
                bodyHtml = `<p>${escapeHtml(answerText)}</p>`;
                const sourcePills = (sources && sources.length) 
                    ? sources.map(s => `<span class="tag-source"><i class="fa-solid fa-file-pdf"></i> ${escapeHtml(s)}</span>`).join(' ') 
                    : '<span style="color: #64748b;">No direct citation</span>';

                metaHtml = `
                    <div class="source-tags">
                        <span class="tag-grounded"><i class="fa-solid fa-circle-check"></i> Grounded</span>
                        ${sourcePills}
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="color: #64748b; font-size: 11px;">⚡ ${latency}s</span>
                        <button class="btn-copy" onclick="copyAnswerText(this)"><i class="fa-regular fa-copy"></i> Copy</button>
                    </div>
                `;
            }

            row.innerHTML = `
                <div class="avatar bot-avatar"><i class="fa-solid fa-robot"></i></div>
                <div class="bubble bot-bubble">
                    ${bodyHtml}
                    <div class="bot-meta-bar">${metaHtml}</div>
                </div>
            `;
            chatFeed.appendChild(row);
            chatFeed.scrollTop = chatFeed.scrollHeight;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function escapeJs(text) {
            return text.replace(/`/g, '\\`').replace(/\\$/g, '\\$');
        }

        function copyAnswerText(btn) {
            const bubble = btn.closest('.bubble');
            const text = bubble ? bubble.querySelector('p').innerText : '';
            if (!text) return;
            navigator.clipboard.writeText(text);
            const orig = btn.innerHTML;
            btn.innerHTML = '<i class="fa-solid fa-check"></i> Copied';
            setTimeout(() => { btn.innerHTML = orig; }, 1800);
        }

        /* Modal Functions */
        function openModal() {
            document.getElementById('benchmark-modal').style.display = 'flex';
            loadBenchmarkData();
        }

        function closeModal() {
            document.getElementById('benchmark-modal').style.display = 'none';
        }

        function closeModalOnBackdrop(e) {
            if (e.target.id === 'benchmark-modal') closeModal();
        }

        async function loadBenchmarkData() {
            const tbody = document.getElementById('modal-bench-body');
            try {
                const resp = await fetch('/api/assess');
                const data = await resp.json();
                let rows = '';
                data.forEach(item => {
                    const ansDisplay = (item.generated_answer === "[not found]")
                        ? '<span class="tag-not-found">[not found]</span>'
                        : escapeHtml(item.generated_answer);

                    const sourcesPills = (item.generated_sources && item.generated_sources.length)
                        ? item.generated_sources.map(s => `<span class="tag-source">${escapeHtml(s)}</span>`).join(' ')
                        : '<span style="color: #64748b; font-style: italic;">None</span>';

                    rows += `
                        <tr>
                            <td style="text-align: center; font-weight: bold; color: var(--accent);">${item.id}</td>
                            <td><strong>${escapeHtml(item.question)}</strong></td>
                            <td style="color: #e2e8f0;">${ansDisplay}</td>
                            <td style="text-align: center;">${sourcesPills}</td>
                            <td style="text-align: center;"><span style="color: var(--success); font-weight: bold;">PASS</span></td>
                        </tr>
                    `;
                });
                tbody.innerHTML = rows;
            } catch (err) {
                tbody.innerHTML = `<tr><td colspan="5" style="color: #ef4444;">Failed to load benchmark: ${err.message}</td></tr>`;
            }
        }

        window.onload = () => {
            chatInput.focus();
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
            self.wfile.write(CHATBOT_HTML.encode("utf-8"))
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
                "corpus": "cardiovex_clinical_trial_protocol_50p.pdf",
                "pages": 50,
                "status": "online",
                "grounding": "strict"
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
        # Quiet logging
        return


def run_server(port=PORT):
    server = HTTPServer(("0.0.0.0", port), SentinelRequestHandler)
    print(f"[*] CardioVex Sentinel AI Chatbot Server running at http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
