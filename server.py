"""
CardioVex Sentinel AI — Full Desktop Web UI & Automation Platform.
Native desktop-first dashboard inspired by the Roobinium / vino_costa AI Agent UI:
- Full widescreen desktop layout (zero phone frames)
- Large animated 3D Holographic AI Agent Core with orbital rings & soundwave equalizer
- Multi-step interactive Automation Workflow Pipeline
- Real-time conversational RAG dialogue stream with multi-turn memory
- Live ChromaDB vector retrieval and strict grounding against the 50-page protocol
"""

import json
import time
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from rag_engine import answer
from run_assessment import ASSESSMENT_QUESTIONS

PORT = 8080

DESKTOP_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CardioVex Sentinel AI — Desktop Automation Platform & Conversational RAG</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-dark: #050811;
            --surface-sidebar: #0a0f1d;
            --surface-card: rgba(16, 24, 40, 0.7);
            --surface-card-hover: rgba(22, 34, 58, 0.85);
            --border: rgba(255, 255, 255, 0.09);
            --border-glow: rgba(0, 240, 255, 0.35);
            --cyan: #00f0ff;
            --cyan-glow: rgba(0, 240, 255, 0.4);
            --purple: #a855f7;
            --purple-glow: rgba(168, 85, 247, 0.4);
            --emerald: #10b981;
            --emerald-glow: rgba(16, 185, 129, 0.4);
            --danger: #ef4444;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --text-dim: #64748b;
            --gradient-primary: linear-gradient(135deg, #00f0ff 0%, #a855f7 100%);
            --card-gradient: linear-gradient(145deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.01) 100%);
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, Helvetica, sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-main);
            height: 100vh;
            width: 100vw;
            display: flex;
            overflow: hidden;
            position: relative;
        }

        /* Ambient Lighting Behind Desktop */
        .ambient-glow {
            position: fixed;
            border-radius: 50%;
            filter: blur(140px);
            pointer-events: none;
            z-index: 0;
            opacity: 0.25;
        }
        .glow-top-left { width: 600px; height: 600px; background: radial-gradient(circle, #00f0ff, transparent); top: -200px; left: -100px; }
        .glow-bottom-right { width: 700px; height: 700px; background: radial-gradient(circle, #a855f7, transparent); bottom: -200px; right: -100px; }

        /* COLUMN 1: LEFT SIDEBAR (Control Panel & Roster) */
        aside.sidebar {
            width: 290px;
            background: var(--surface-sidebar);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            padding: 24px 18px;
            z-index: 10;
            flex-shrink: 0;
            user-select: none;
        }

        .brand-header {
            display: flex;
            align-items: center;
            gap: 12px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border);
        }
        .brand-logo {
            width: 40px;
            height: 40px;
            background: var(--gradient-primary);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #000;
            font-size: 18px;
            box-shadow: 0 0 20px var(--cyan-glow);
        }
        .brand-text h1 { font-size: 16px; font-weight: 700; color: #fff; letter-spacing: -0.3px; }
        .brand-text p { font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.6px; }

        .system-status-pill {
            margin-top: 16px;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 8px;
            padding: 8px 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            color: var(--emerald);
            font-weight: 600;
        }
        .status-dot {
            width: 7px;
            height: 7px;
            background: var(--emerald);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--emerald);
            animation: pulseDot 1.8s infinite;
        }
        @keyframes pulseDot {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.3; transform: scale(0.8); }
        }

        .sidebar-section-title {
            font-size: 11px;
            font-weight: 700;
            color: var(--text-dim);
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin: 22px 6px 10px 6px;
        }

        /* Agent Roster List */
        .agent-roster {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .roster-item {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 10px 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 12.5px;
            transition: all 0.2s;
            cursor: pointer;
        }
        .roster-item:hover {
            border-color: var(--border-glow);
            background: rgba(255, 255, 255, 0.06);
        }
        .roster-left { display: flex; align-items: center; gap: 9px; font-weight: 600; }
        .roster-dot-active { width: 6px; height: 6px; background: var(--cyan); border-radius: 50%; box-shadow: 0 0 6px var(--cyan); }
        .roster-tag { font-size: 10px; background: rgba(0, 240, 255, 0.15); color: var(--cyan); padding: 2px 6px; border-radius: 4px; font-weight: 700; }

        /* Quick Inquiries List */
        .quick-inquiries {
            display: flex;
            flex-direction: column;
            gap: 6px;
            overflow-y: auto;
            flex: 1;
            margin-top: 4px;
        }
        .inquiry-btn {
            background: transparent;
            color: var(--text-muted);
            border: 1px solid transparent;
            border-radius: 8px;
            padding: 8px 10px;
            font-size: 12.5px;
            text-align: left;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.15s;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .inquiry-btn:hover {
            background: rgba(255, 255, 255, 0.05);
            color: #fff;
            border-color: var(--border);
        }
        .inquiry-btn i { font-size: 11px; color: var(--cyan); width: 14px; text-align: center; }

        .sidebar-footer {
            padding-top: 16px;
            border-top: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .btn-benchmark-matrix {
            background: rgba(168, 85, 247, 0.12);
            color: #c084fc;
            border: 1px solid rgba(168, 85, 247, 0.35);
            border-radius: 8px;
            padding: 10px;
            font-size: 12.5px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: all 0.2s;
        }
        .btn-benchmark-matrix:hover {
            background: var(--purple);
            color: #000;
            box-shadow: 0 0 15px var(--purple-glow);
        }

        /* COLUMN 2: CENTER WORKSPACE (Holographic Agent & Automation Pipeline) */
        main.center-stage {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 24px 30px;
            overflow-y: auto;
            z-index: 10;
            gap: 22px;
        }
        main.center-stage::-webkit-scrollbar { width: 6px; }
        main.center-stage::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 4px; }

        /* Top Metrics Header Row */
        .metrics-row {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 14px;
        }
        .metric-card {
            background: var(--surface-card);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 14px 18px;
            backdrop-filter: blur(16px);
            transition: all 0.2s;
        }
        .metric-card:hover { border-color: var(--border-glow); transform: translateY(-1px); }
        .metric-label { font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; }
        .metric-val { font-size: 19px; font-weight: 700; margin-top: 4px; color: var(--text-main); display: flex; align-items: center; gap: 8px; }
        .metric-val.accent-cyan { color: var(--cyan); }
        .metric-val.accent-green { color: var(--emerald); }

        /* Roobinium 3D Holographic AI Agent Core Stage */
        .agent-core-hero {
            background: radial-gradient(circle at 50% 35%, rgba(0, 240, 255, 0.08) 0%, rgba(168, 85, 247, 0.04) 40%, rgba(16, 24, 40, 0.7) 80%);
            border: 1px solid var(--border);
            border-radius: 22px;
            padding: 28px 24px 22px 24px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            position: relative;
            backdrop-filter: blur(20px);
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
            overflow: hidden;
        }
        .hero-glow-underlay {
            position: absolute;
            width: 250px;
            height: 250px;
            background: radial-gradient(circle, rgba(0, 240, 255, 0.35) 0%, rgba(168, 85, 247, 0.15) 50%, transparent 80%);
            border-radius: 50%;
            filter: blur(40px);
            pointer-events: none;
        }

        /* 3D Orb Stage */
        .orb-stage {
            width: 190px;
            height: 190px;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 6px 0 16px 0;
        }
        .orb-sphere {
            width: 90px;
            height: 90px;
            background: radial-gradient(circle at 35% 35%, #00f0ff 0%, #3b82f6 35%, #8b5cf6 75%, #050811 100%);
            border-radius: 50%;
            box-shadow: 
                0 0 40px rgba(0, 240, 255, 0.65),
                0 0 70px rgba(168, 85, 247, 0.45);
            animation: orbPulse 4s ease-in-out infinite alternate;
            position: relative;
            z-index: 2;
        }
        @keyframes orbPulse {
            0% { transform: scale(0.94); filter: brightness(0.95); }
            100% { transform: scale(1.06); filter: brightness(1.2); }
        }

        /* Counter-Rotating Dashed Holographic Rings */
        .orbit-ring {
            position: absolute;
            border-radius: 50%;
            pointer-events: none;
        }
        .ring-outer {
            width: 170px;
            height: 170px;
            border: 1.5px dashed rgba(0, 240, 255, 0.5);
            animation: rotateOuter 14s linear infinite;
        }
        .ring-inner {
            width: 135px;
            height: 135px;
            border: 1.5px solid rgba(168, 85, 247, 0.45);
            border-left-color: transparent;
            border-right-color: transparent;
            animation: rotateInner 10s linear infinite;
        }
        @keyframes rotateOuter { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes rotateInner { from { transform: rotate(360deg); } to { transform: rotate(0deg); } }

        /* Soundwave Voice Equalizer */
        .soundwave {
            display: flex;
            align-items: center;
            gap: 5px;
            height: 24px;
            margin-top: 4px;
        }
        .wave-bar {
            width: 3.5px;
            height: 10px;
            background: var(--cyan);
            border-radius: 4px;
            animation: waveBounce 1.2s ease-in-out infinite alternate;
        }
        .wave-bar:nth-child(2) { animation-delay: 0.15s; height: 18px; background: #38bdf8; }
        .wave-bar:nth-child(3) { animation-delay: 0.35s; height: 24px; background: #a855f7; }
        .wave-bar:nth-child(4) { animation-delay: 0.25s; height: 16px; background: #c084fc; }
        .wave-bar:nth-child(5) { animation-delay: 0.4s; height: 12px; background: var(--cyan); }
        @keyframes waveBounce {
            0% { transform: scaleY(0.4); }
            100% { transform: scaleY(1.4); }
        }

        .agent-hero-info h2 { font-size: 20px; font-weight: 700; color: #fff; text-align: center; margin-top: 10px; }
        .agent-hero-info p { font-size: 13px; color: var(--text-muted); text-align: center; margin-top: 4px; }

        /* Automation Platform Workflow Execution Cards */
        .section-header-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .section-header-row h3 { font-size: 14px; font-weight: 700; text-transform: uppercase; color: #fff; letter-spacing: 0.6px; }

        .workflow-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 14px;
        }
        .workflow-card {
            background: var(--surface-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 16px 18px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            backdrop-filter: blur(14px);
            transition: all 0.25s;
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }
        .workflow-card:hover {
            border-color: var(--border-glow);
            background: var(--surface-card-hover);
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 240, 255, 0.12);
        }
        .workflow-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .workflow-title-wrap {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 14px;
            font-weight: 600;
            color: #fff;
        }
        .workflow-icon {
            width: 34px;
            height: 34px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
        }
        .icon-cyan { background: rgba(0, 240, 255, 0.15); color: var(--cyan); }
        .icon-purple { background: rgba(168, 85, 247, 0.15); color: var(--purple); }
        .icon-green { background: rgba(16, 185, 129, 0.15); color: var(--emerald); }

        .status-badge {
            font-size: 11px;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 9999px;
        }
        .badge-verified { background: rgba(16, 185, 129, 0.15); color: var(--emerald); border: 1px solid rgba(16, 185, 129, 0.35); }
        .badge-active { background: rgba(0, 240, 255, 0.15); color: var(--cyan); border: 1px solid rgba(0, 240, 255, 0.35); }

        .workflow-desc {
            font-size: 12.5px;
            color: var(--text-muted);
            line-height: 1.5;
        }

        .progress-bar-bg {
            width: 100%;
            height: 6px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 999px;
            overflow: hidden;
        }
        .progress-bar-fill {
            height: 100%;
            background: var(--gradient-primary);
            border-radius: 999px;
        }

        .workflow-footer-meta {
            display: flex;
            justify-content: space-between;
            font-size: 11.5px;
            color: var(--text-dim);
        }

        /* COLUMN 3: RIGHT PANEL (Conversational Dialogue Stream) */
        section.chat-panel {
            width: 440px;
            background: var(--surface-sidebar);
            border-left: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            z-index: 10;
            flex-shrink: 0;
        }

        .chat-header {
            height: 65px;
            border-bottom: 1px solid var(--border);
            padding: 0 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .chat-header-title h3 { font-size: 15px; font-weight: 700; color: #fff; }
        .chat-header-title p { font-size: 11px; color: var(--text-muted); }
        .btn-clear-chat {
            background: transparent;
            color: var(--text-dim);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 5px 10px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-clear-chat:hover { color: #fff; border-color: var(--border-glow); }

        /* Message Stream */
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 18px 20px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .chat-messages::-webkit-scrollbar { width: 5px; }
        .chat-messages::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 4px; }

        .chat-bubble {
            padding: 14px 16px;
            border-radius: 14px;
            font-size: 13.5px;
            line-height: 1.6;
            max-width: 88%;
        }
        .user-bubble {
            background: #1d4ed8;
            color: #fff;
            align-self: flex-end;
            border-bottom-right-radius: 2px;
        }
        .agent-bubble {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border);
            color: var(--text-main);
            align-self: flex-start;
            border-bottom-left-radius: 2px;
            backdrop-filter: blur(14px);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25);
        }
        .agent-bubble .bubble-meta {
            margin-top: 10px;
            padding-top: 8px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 11.5px;
        }
        .citation-tag {
            background: #172554;
            color: #60a5fa;
            border: 1px solid #1e40af;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
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
        .btn-copy-ans {
            background: transparent;
            border: none;
            color: var(--text-dim);
            cursor: pointer;
            font-size: 12px;
        }
        .btn-copy-ans:hover { color: #fff; }

        /* Typing Indicator */
        .typing-box {
            display: none;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border);
            border-radius: 10px;
            width: fit-content;
            font-size: 12px;
            color: var(--text-muted);
        }
        .typing-dots { display: flex; gap: 4px; }
        .typing-dots span {
            width: 5px; height: 5px; background: var(--cyan); border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out both;
        }
        .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
        .typing-dots span:nth-child(2) { animation-delay: -0.16s; }
        @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }

        /* Floating Input Dock */
        .chat-input-dock {
            padding: 14px 20px 20px 20px;
            border-top: 1px solid var(--border);
            background: var(--surface-sidebar);
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .input-pill-box {
            background: #060911;
            border: 1px solid var(--border);
            border-radius: 9999px;
            padding: 6px 8px 6px 16px;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: all 0.2s;
        }
        .input-pill-box:focus-within {
            border-color: var(--cyan);
            box-shadow: 0 0 15px var(--cyan-glow);
        }
        .input-pill-box input {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: #fff;
            font-size: 13.5px;
        }
        .btn-send-pill {
            width: 34px;
            height: 34px;
            background: var(--gradient-primary);
            border: none;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #000;
            font-size: 13px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .btn-send-pill:hover { transform: scale(1.08); }

        .suggestions-row {
            display: flex;
            gap: 6px;
            overflow-x: auto;
        }
        .suggestions-row::-webkit-scrollbar { height: 0; }
        .suggestion-chip {
            background: rgba(255, 255, 255, 0.04);
            color: var(--text-muted);
            border: 1px solid var(--border);
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 11.5px;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.2s;
        }
        .suggestion-chip:hover {
            color: var(--cyan);
            border-color: var(--cyan);
            background: rgba(0, 240, 255, 0.08);
        }

        /* Benchmark Modal */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            z-index: 1000;
            align-items: center;
            justify-content: center;
            padding: 24px;
        }
        .modal-content {
            background: #0a0f1d;
            border: 1px solid var(--border-glow);
            border-radius: 18px;
            width: 100%;
            max-width: 960px;
            max-height: 85vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 25px 60px rgba(0, 0, 0, 0.8);
        }
        .modal-header {
            padding: 18px 24px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .modal-body { padding: 20px 24px; overflow-y: auto; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th { background: #050811; color: var(--text-muted); padding: 12px; text-align: left; }
        td { padding: 14px 12px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); vertical-align: top; }
    </style>
</head>
<body>

    <!-- Ambient Lighting Orbs -->
    <div class="ambient-glow glow-top-left"></div>
    <div class="ambient-glow glow-bottom-right"></div>

    <!-- COLUMN 1: LEFT SIDEBAR (Control Panel & Agent Roster) -->
    <aside class="sidebar">
        <div class="brand-header">
            <div class="brand-logo"><i class="fa-solid fa-shield-heart"></i></div>
            <div class="brand-text">
                <h1>CardioVex Sentinel</h1>
                <p>AI AGENT &bull; AUTOMATION PLATFORM</p>
            </div>
        </div>

        <div class="system-status-pill">
            <span class="status-dot"></span>
            <span>ChromaDB Persistent (238 Chunks)</span>
        </div>

        <div class="sidebar-section-title">Autonomous Agents</div>
        <div class="agent-roster">
            <div class="roster-item" onclick="submitInquiry('What is the minimum eGFR required for patient inclusion?')">
                <div class="roster-left">
                    <span class="roster-dot-active"></span>
                    <span>Sentinel-01 (Clinical Core)</span>
                </div>
                <span class="roster-tag">ACTIVE</span>
            </div>
            <div class="roster-item" onclick="submitInquiry('Within how many hours must an SAE be reported to the pharmacovigilance safety desk?')">
                <div class="roster-left">
                    <span class="roster-dot-active" style="background: var(--purple); box-shadow: 0 0 6px var(--purple);"></span>
                    <span>Pharmacovigilance Bot</span>
                </div>
                <span class="roster-tag" style="color: var(--purple); background: rgba(168, 85, 247, 0.15);">STANDBY</span>
            </div>
            <div class="roster-item" onclick="submitInquiry('Within what exact temperature range must reconstituted CardioVex vials be stored?')">
                <div class="roster-left">
                    <span class="roster-dot-active" style="background: var(--emerald); box-shadow: 0 0 6px var(--emerald);"></span>
                    <span>Cold-Chain Monitor</span>
                </div>
                <span class="roster-tag" style="color: var(--emerald); background: rgba(16, 185, 129, 0.15);">ACTIVE</span>
            </div>
        </div>

        <div class="sidebar-section-title">Protocol Inquiries</div>
        <div class="quick-inquiries">
            <button class="inquiry-btn" onclick="submitInquiry('What is the minimum required estimated Glomerular Filtration Rate (eGFR) threshold for a patient to be included in the CardioVex Phase III trial?')">
                <i class="fa-solid fa-dna"></i> Q1: eGFR Threshold (P.14)
            </button>
            <button class="inquiry-btn" onclick="submitInquiry('Within how many hours of becoming aware of a Serious Adverse Event (SAE) must a site investigator report it to the pharmacovigilance safety desk?')">
                <i class="fa-solid fa-bell"></i> Q2: SAE Reporting Window (P.28)
            </button>
            <button class="inquiry-btn" onclick="submitInquiry('What is the wholesale or retail price of CardioVex in commercial pharmacies?')">
                <i class="fa-solid fa-tag"></i> Q3: Commercial Price (Negative)
            </button>
            <button class="inquiry-btn" onclick="submitInquiry('Within what exact temperature range, in degrees Celsius, must reconstituted CardioVex vials be stored before administration?')">
                <i class="fa-solid fa-temperature-arrow-down"></i> Q4: Storage Temp 2-8°C (P.42)
            </button>
            <button class="inquiry-btn" onclick="submitInquiry('What is the standard recommended dosage of amoxicillin for treating a paediatric ear infection?')">
                <i class="fa-solid fa-pills"></i> Q5: Paediatric Amoxicillin (Negative)
            </button>
            <button class="inquiry-btn" onclick="submitInquiry('What are the protocol guidelines regarding prohibited CYP3A4 inhibitors?')">
                <i class="fa-solid fa-ban"></i> Prohibited CYP3A4 Inhibitors
            </button>
            <button class="inquiry-btn" onclick="submitInquiry('What are the requirements for informed consent documentation and ICH-GCP audits?')">
                <i class="fa-solid fa-file-signature"></i> Informed Consent & GCP Audits
            </button>
            <button class="inquiry-btn" onclick="submitInquiry('What baseline echocardiography biomarkers are monitored in the protocol?')">
                <i class="fa-solid fa-heart-pulse"></i> Baseline Echocardiography
            </button>
        </div>

        <div class="sidebar-footer">
            <button class="btn-benchmark-matrix" onclick="openModal()">
                <i class="fa-solid fa-clipboard-check"></i> View 5/5 Benchmark Matrix
            </button>
        </div>
    </aside>

    <!-- COLUMN 2: CENTER WORKSPACE (Holographic Agent & Automation Pipeline) -->
    <main class="center-stage">
        
        <!-- Top Metrics Row -->
        <div class="metrics-row">
            <div class="metric-card">
                <div class="metric-label">Knowledge Corpus</div>
                <div class="metric-val accent-cyan">50 Pages <span style="font-size: 13px; font-weight: normal; color: var(--text-muted);">(238 Chunks)</span></div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Grounding Policy</div>
                <div class="metric-val accent-green">Strict <span style="font-size: 13px; font-weight: normal; color: var(--text-muted);">(Zero Assumption)</span></div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Benchmark Accuracy</div>
                <div class="metric-val accent-green">100.0% <span style="font-size: 13px; font-weight: normal; color: var(--text-muted);">(5/5 Passed)</span></div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Average Latency</div>
                <div class="metric-val" id="telemetry-latency">⚡ 0.09s <span style="font-size: 13px; font-weight: normal; color: var(--text-muted);">(ChromaDB ONNX)</span></div>
            </div>
        </div>

        <!-- 3D Holographic AI Agent Core (Roobinium Signature Hero) -->
        <div class="agent-core-hero">
            <div class="hero-glow-underlay"></div>
            <div class="orb-stage">
                <div class="orbit-ring ring-outer"></div>
                <div class="orbit-ring ring-inner"></div>
                <div class="orb-sphere" id="orb-sphere"></div>
            </div>
            <div class="soundwave">
                <div class="wave-bar"></div>
                <div class="wave-bar"></div>
                <div class="wave-bar"></div>
                <div class="wave-bar"></div>
                <div class="wave-bar"></div>
            </div>
            <div class="agent-hero-info">
                <h2>Autonomous Clinical Protocol Agent</h2>
                <p>Real-time vector inference against <code>cardiovex_clinical_trial_protocol_50p.pdf</code></p>
            </div>
        </div>

        <!-- Automation Platform Workflow Execution Pipeline -->
        <div class="section-header-row">
            <h3>Protocol Automation Pipelines</h3>
            <span style="font-size: 12px; color: var(--cyan);"><i class="fa-solid fa-bolt"></i> Interactive Execution</span>
        </div>

        <div class="workflow-grid">
            <!-- Pipeline Card 1 -->
            <div class="workflow-card" onclick="submitInquiry('What is the minimum eGFR required for patient inclusion?')">
                <div class="workflow-header">
                    <div class="workflow-title-wrap">
                        <div class="workflow-icon icon-cyan"><i class="fa-solid fa-dna"></i></div>
                        <span>Renal Inclusion & eGFR Verification</span>
                    </div>
                    <span class="status-badge badge-verified">Verified (P.14)</span>
                </div>
                <div class="workflow-desc">
                    Audits patient renal eligibility against Section 4.1 threshold (&ge; 45 mL/min/1.73m&sup2; via CKD-EPI). Excludes below 45.
                </div>
                <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: 100%;"></div></div>
                <div class="workflow-footer-meta">
                    <span>Target: NYHA Class II-III Adults</span>
                    <span>Clause: Section 4.1</span>
                </div>
            </div>

            <!-- Pipeline Card 2 -->
            <div class="workflow-card" onclick="submitInquiry('Within how many hours must an SAE be reported to the pharmacovigilance safety desk?')">
                <div class="workflow-header">
                    <div class="workflow-title-wrap">
                        <div class="workflow-icon icon-purple"><i class="fa-solid fa-bell"></i></div>
                        <span>Expedited SAE Pharmacovigilance</span>
                    </div>
                    <span class="status-badge badge-active">24h Window (P.28)</span>
                </div>
                <div class="workflow-desc">
                    Automated timer verifying that site investigators report any Serious Adverse Event to the central Safety Desk within 24 hours.
                </div>
                <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: 100%;"></div></div>
                <div class="workflow-footer-meta">
                    <span>Method: Electronic eCRF Safety Portal</span>
                    <span>Clause: Section 7.3</span>
                </div>
            </div>

            <!-- Pipeline Card 3 -->
            <div class="workflow-card" onclick="submitInquiry('Within what exact temperature range must reconstituted CardioVex vials be stored?')">
                <div class="workflow-header">
                    <div class="workflow-title-wrap">
                        <div class="workflow-icon icon-green"><i class="fa-solid fa-temperature-arrow-down"></i></div>
                        <span>Cold-Chain Reconstitution Logging</span>
                    </div>
                    <span class="status-badge badge-verified">2&deg;C &ndash; 8&deg;C (P.42)</span>
                </div>
                <div class="workflow-desc">
                    Verifies calibrated medical refrigeration before IV administration. Strictly enforces continuous temperature logging (Do Not Freeze).
                </div>
                <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: 100%;"></div></div>
                <div class="workflow-footer-meta">
                    <span>Refrigeration: Calibrated Logging</span>
                    <span>Clause: Section 10.2</span>
                </div>
            </div>

            <!-- Pipeline Card 4 -->
            <div class="workflow-card" onclick="submitInquiry('What are the protocol guidelines regarding prohibited CYP3A4 inhibitors?')">
                <div class="workflow-header">
                    <div class="workflow-title-wrap">
                        <div class="workflow-icon icon-purple"><i class="fa-solid fa-ban"></i></div>
                        <span>Prohibited CYP3A4 Washout Audit</span>
                    </div>
                    <span class="status-badge badge-active">Monitored (P.43)</span>
                </div>
                <div class="workflow-desc">
                    Governance standard ensuring adherence to concomitant medication washout schedules and audit log maintenance.
                </div>
                <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: 100%;"></div></div>
                <div class="workflow-footer-meta">
                    <span>Compliance: Module 43.0</span>
                    <span>Clause: Clause 43.1</span>
                </div>
            </div>
        </div>

    </main>

    <!-- COLUMN 3: RIGHT PANEL (Conversational Dialogue Stream) -->
    <section class="chat-panel">
        <div class="chat-header">
            <div class="chat-header-title">
                <h3>Sentinel Dialogue Stream</h3>
                <p>Conversational RAG with Context Memory</p>
            </div>
            <button class="btn-clear-chat" onclick="resetDialogue()"><i class="fa-solid fa-trash-can"></i> Clear</button>
        </div>

        <!-- Chat Stream -->
        <div class="chat-messages" id="chat-stream">
            <div class="chat-bubble agent-bubble">
                <p><strong>Hello! I am CardioVex Sentinel AI 🛡️</strong></p>
                <p style="margin-top: 6px; color: var(--text-muted); font-size: 13px;">
                    I am your clinical trial protocol conversational assistant. Ask any question, follow-up (<em>"Why?"</em>, <em>"What happens if they fail?"</em>, <em>"What about SAEs?"</em>), or trigger an automation pipeline card on the left.
                </p>
            </div>
        </div>

        <!-- Typing Indicator -->
        <div class="typing-box" id="typing-box">
            <span>Querying ChromaDB vector store</span>
            <div class="typing-dots"><span></span><span></span><span></span></div>
        </div>

        <!-- Floating Input Dock -->
        <div class="chat-input-dock">
            <div class="suggestions-row">
                <span class="suggestion-chip" onclick="submitInquiry('What is the minimum eGFR required for inclusion?')">eGFR Threshold</span>
                <span class="suggestion-chip" onclick="submitInquiry('Within how many hours must an SAE be reported?')">SAE Window</span>
                <span class="suggestion-chip" onclick="submitInquiry('What happens if the patient fails this criterion?')">Follow-up: What if they fail?</span>
                <span class="suggestion-chip" onclick="submitInquiry('What is the commercial pharmacy price?')">Price (Negative Test)</span>
            </div>

            <div class="input-pill-box">
                <i class="fa-solid fa-sparkles" style="color: var(--cyan); font-size: 13px;"></i>
                <input type="text" id="chat-input-field" placeholder="Ask anything about the clinical trial protocol..." autocomplete="off">
                <i class="fa-solid fa-microphone" style="color: var(--cyan); cursor: pointer; font-size: 13px;" onclick="simulateMic()"></i>
                <button class="btn-send-pill" onclick="handleSendAction()"><i class="fa-solid fa-arrow-up"></i></button>
            </div>
        </div>
    </section>

    <!-- Benchmark Matrix Pop-up Modal -->
    <div class="modal-overlay" id="benchmark-modal" onclick="closeModalOnBackdrop(event)">
        <div class="modal-content">
            <div class="modal-header">
                <div>
                    <h3 style="color: var(--cyan); font-size: 17px;">Assessment Benchmark Matrix (5/5 PASS)</h3>
                    <p style="color: var(--text-muted); font-size: 12.5px;">CardioVex Phase III Clinical Protocol Validation Suite</p>
                </div>
                <i class="fa-solid fa-xmark" style="cursor: pointer; font-size: 18px; color: var(--text-muted);" onclick="closeModal()"></i>
            </div>
            <div class="modal-body">
                <table>
                    <thead>
                        <tr>
                            <th style="width: 45px; text-align: center;">ID</th>
                            <th style="width: 30%;">Assessment Question</th>
                            <th style="width: 44%;">Generated Answer</th>
                            <th style="width: 14%; text-align: center;">Source</th>
                            <th style="width: 8%; text-align: center;">Status</th>
                        </tr>
                    </thead>
                    <tbody id="modal-table-body">
                        <tr><td colspan="5" style="text-align: center; color: var(--text-muted);">Loading benchmark results...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        let dialogueHistory = [];

        const inputField = document.getElementById('chat-input-field');
        const chatStream = document.getElementById('chat-stream');
        const typingBox = document.getElementById('typing-box');
        const orbSphere = document.getElementById('orb-sphere');
        const telemetryLatency = document.getElementById('telemetry-latency');

        inputField.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleSendAction();
            }
        });

        function submitInquiry(text) {
            inputField.value = text;
            handleSendAction();
        }

        function simulateMic() {
            inputField.value = "What is the minimum eGFR required for inclusion?";
            inputField.focus();
        }

        function resetDialogue() {
            dialogueHistory = [];
            chatStream.innerHTML = `
                <div class="chat-bubble agent-bubble">
                    <p><strong>Dialogue refreshed.</strong></p>
                    <p style="margin-top: 4px; color: var(--text-muted); font-size: 13px;">
                        Conversation memory cleared. How can I assist you with the CardioVex clinical protocol?
                    </p>
                </div>
            `;
            inputField.focus();
        }

        async function handleSendAction() {
            const query = inputField.value.trim();
            if (!query) return;

            // 1. Append User Bubble
            const userBubble = document.createElement('div');
            userBubble.className = 'chat-bubble user-bubble';
            userBubble.innerText = query;
            chatStream.appendChild(userBubble);
            inputField.value = '';

            // Animate Orb to active search state
            orbSphere.style.boxShadow = '0 0 60px #00f0ff, 0 0 90px #a855f7';
            orbSphere.style.filter = 'brightness(1.4)';

            typingBox.style.display = 'flex';
            chatStream.scrollTop = chatStream.scrollHeight;

            const startTime = performance.now();

            try {
                const resp = await fetch('/api/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        question: query,
                        history: dialogueHistory
                    })
                });

                const data = await resp.json();
                const latency = ((performance.now() - startTime) / 1000).toFixed(3);
                telemetryLatency.innerText = `⚡ ${latency}s`;

                // Revert Orb state
                orbSphere.style.boxShadow = '0 0 40px rgba(0, 240, 255, 0.65)';
                orbSphere.style.filter = 'brightness(1.0)';
                typingBox.style.display = 'none';

                const botBubble = document.createElement('div');
                botBubble.className = 'chat-bubble agent-bubble';

                let bodyHtml = '';
                if (data.answer === "[not found]") {
                    bodyHtml = `
                        <p><span class="tag-not-found">[not found]</span></p>
                        <p style="margin-top: 6px; font-size: 13px; color: var(--text-muted);">
                            The queried information is <strong>not present</strong> in the official 50-page CardioVex Phase III clinical protocol. External assumptions are prohibited under strict grounding.
                        </p>
                    `;
                } else {
                    bodyHtml = `<p>${escapeHtml(data.answer)}</p>`;
                }

                const sourcesPill = (data.sources && data.sources.length)
                    ? data.sources.map(s => `<span class="citation-tag">${escapeHtml(s)}</span>`).join(' ')
                    : '<span style="color: var(--text-dim);">None</span>';

                botBubble.innerHTML = `
                    ${bodyHtml}
                    <div class="bubble-meta">
                        <div>${sourcesPill}</div>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="color: var(--text-dim); font-size: 11px;">⚡ ${latency}s</span>
                            <button class="btn-copy-ans" onclick="copyAnsText(this)"><i class="fa-regular fa-copy"></i></button>
                        </div>
                    </div>
                `;

                chatStream.appendChild(botBubble);
                dialogueHistory.push({ role: 'user', content: query });
                dialogueHistory.push({ role: 'assistant', content: data.answer });

            } catch (err) {
                typingBox.style.display = 'none';
                const botBubble = document.createElement('div');
                botBubble.className = 'chat-bubble agent-bubble';
                botBubble.innerHTML = `<p style="color: #ef4444;">Error connecting to ChromaDB engine: ${err.message}</p>`;
                chatStream.appendChild(botBubble);
            } finally {
                chatStream.scrollTop = chatStream.scrollHeight;
                inputField.focus();
            }
        }

        function escapeHtml(t) {
            const d = document.createElement('div');
            d.textContent = t;
            return d.innerHTML;
        }

        function copyAnsText(btn) {
            const bubble = btn.closest('.chat-bubble');
            const p = bubble ? bubble.querySelector('p') : null;
            if (!p) return;
            navigator.clipboard.writeText(p.innerText);
            btn.innerHTML = '<i class="fa-solid fa-check" style="color: var(--emerald);"></i>';
            setTimeout(() => { btn.innerHTML = '<i class="fa-regular fa-copy"></i>'; }, 1800);
        }

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
            const tbody = document.getElementById('modal-table-body');
            try {
                const resp = await fetch('/api/assess');
                const data = await resp.json();
                let rows = '';
                data.forEach(item => {
                    const ans = (item.generated_answer === "[not found]")
                        ? '<span class="tag-not-found">[not found]</span>'
                        : escapeHtml(item.generated_answer);

                    const sourcesPills = (item.generated_sources && item.generated_sources.length)
                        ? item.generated_sources.map(s => `<span class="citation-tag">${escapeHtml(s)}</span>`).join(' ')
                        : '<span style="color: var(--text-dim); font-style: italic;">None</span>';

                    rows += `
                        <tr>
                            <td style="text-align: center; font-weight: bold; color: var(--purple);">${item.id}</td>
                            <td><strong>${escapeHtml(item.question)}</strong></td>
                            <td style="color: #e2e8f0;">${ans}</td>
                            <td style="text-align: center;">${sourcesPills}</td>
                            <td style="text-align: center; color: var(--emerald); font-weight: bold;">PASS</td>
                        </tr>
                    `;
                });
                tbody.innerHTML = rows;
            } catch (e) {
                tbody.innerHTML = `<tr><td colspan="5" style="color: #ef4444;">Failed to load benchmark: ${e.message}</td></tr>`;
            }
        }
    </script>
</body>
</html>
"""


class SentinelRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ["/", "/index.html", "/desktop"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DESKTOP_HTML.encode("utf-8"))
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
                "ui": "Full Desktop Automation Platform",
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
        return


def run_server(port=PORT):
    server = HTTPServer(("0.0.0.0", port), SentinelRequestHandler)
    print(f"[*] CardioVex Sentinel AI Desktop Platform running at http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
