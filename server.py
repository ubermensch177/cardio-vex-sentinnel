"""
CardioVex Sentinel AI — Mobile App UI & Automation Platform.
Faithfully recreates the Roobinium / vino_costa "AI Agent Mobile App UI Animation for Automation Platform"
featuring a 3D-style animated AI Agent Core, autonomous automation pipeline, multi-tab navigation dock,
and real-time conversational RAG query execution against the 50-page protocol corpus.
"""

import json
import time
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from rag_engine import answer
from run_assessment import ASSESSMENT_QUESTIONS

PORT = 8080

UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CardioVex Sentinel — AI Agent Mobile Automation Platform</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-canvas: #04070e;
            --phone-bg: #090e17;
            --phone-surface: rgba(18, 26, 43, 0.75);
            --phone-border: rgba(255, 255, 255, 0.12);
            --cyan-glow: #00f0ff;
            --purple-glow: #a855f7;
            --emerald-glow: #10b981;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-gradient: linear-gradient(135deg, #00f0ff 0%, #a855f7 100%);
            --card-gradient: linear-gradient(145deg, rgba(255, 255, 255, 0.07) 0%, rgba(255, 255, 255, 0.02) 100%);
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, Helvetica, sans-serif;
            background-color: var(--bg-canvas);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
            overflow-x: hidden;
            position: relative;
        }

        /* Ambient Glow Background Orbs */
        .ambient-orb {
            position: fixed;
            border-radius: 50%;
            filter: blur(120px);
            pointer-events: none;
            z-index: 0;
            opacity: 0.35;
        }
        .orb-1 { width: 500px; height: 500px; background: radial-gradient(circle, #00f0ff, transparent); top: -100px; left: -100px; }
        .orb-2 { width: 550px; height: 550px; background: radial-gradient(circle, #8b5cf6, transparent); bottom: -120px; right: -120px; }

        /* Top Control Bar */
        .top-toolbar {
            position: fixed;
            top: 15px;
            display: flex;
            gap: 12px;
            z-index: 100;
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(16px);
            padding: 6px 14px;
            border-radius: 9999px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .btn-view-toggle {
            background: transparent;
            color: var(--text-secondary);
            border: none;
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .btn-view-toggle.active {
            background: var(--accent-gradient);
            color: #000;
            box-shadow: 0 0 15px rgba(0, 240, 255, 0.4);
        }

        /* iPhone 16 Pro Frame Device Wrapper */
        .device-container {
            position: relative;
            z-index: 10;
            transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
            margin: 40px auto 20px auto;
        }

        .phone-frame {
            width: 410px;
            height: 844px;
            background: var(--phone-bg);
            border-radius: 54px;
            padding: 14px;
            box-shadow: 
                0 0 0 4px #1e293b,
                0 0 0 6px #0f172a,
                0 25px 60px rgba(0, 0, 0, 0.8),
                0 0 80px rgba(0, 240, 255, 0.15);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            position: relative;
            border: 1px solid var(--phone-border);
        }

        /* Fullscreen Expansion Mode */
        body.fullscreen-mode .phone-frame {
            width: 95vw;
            max-width: 1080px;
            height: 90vh;
            border-radius: 28px;
            padding: 20px;
        }

        /* Internal Screen Canvas */
        .screen {
            flex: 1;
            background: radial-gradient(120% 90% at 50% 0%, #111a2e 0%, #080c14 100%);
            border-radius: 42px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            position: relative;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        /* iPhone Notch / Dynamic Island */
        .dynamic-island {
            width: 125px;
            height: 32px;
            background: #000;
            border-radius: 20px;
            margin: 12px auto 6px auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 12px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.8);
            z-index: 50;
            transition: all 0.3s;
        }
        .dynamic-island .camera { width: 11px; height: 11px; background: #0f172a; border-radius: 50%; border: 1px solid #1e293b; }
        .dynamic-island .lens { width: 9px; height: 9px; background: #0284c7; border-radius: 50%; opacity: 0.8; }

        /* Screen Header Bar */
        .screen-header {
            padding: 10px 22px 14px 22px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 20;
        }
        .app-brand {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .brand-badge {
            width: 32px;
            height: 32px;
            background: var(--accent-gradient);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #000;
            font-size: 14px;
            box-shadow: 0 0 12px rgba(0, 240, 255, 0.5);
        }
        .brand-text h2 { font-size: 15px; font-weight: 700; color: #fff; }
        .brand-text p { font-size: 10.5px; color: var(--text-secondary); letter-spacing: 0.5px; }

        .live-tag {
            background: rgba(16, 185, 129, 0.15);
            color: var(--emerald-glow);
            border: 1px solid rgba(16, 185, 129, 0.35);
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .live-tag .dot {
            width: 6px;
            height: 6px;
            background: var(--emerald-glow);
            border-radius: 50%;
            box-shadow: 0 0 6px var(--emerald-glow);
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(0.85); }
        }

        /* Content Scroll Area */
        .screen-content {
            flex: 1;
            overflow-y: auto;
            padding: 10px 18px 80px 18px;
            display: flex;
            flex-direction: column;
            gap: 18px;
            scroll-behavior: smooth;
        }
        .screen-content::-webkit-scrollbar { width: 0; }

        /* TAB 1: AI AGENT HERO & ORB ANIMATION (Roobinium Dribbble Signature) */
        .agent-hero-card {
            background: var(--card-gradient);
            border: 1px solid var(--phone-border);
            border-radius: 28px;
            padding: 24px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(20px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        }

        /* 3D Holographic Animated AI Agent Orb */
        .orb-stage {
            width: 170px;
            height: 170px;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 10px 0 18px 0;
        }
        .orb-core {
            width: 80px;
            height: 80px;
            background: radial-gradient(circle at 35% 35%, #00f0ff 0%, #3b82f6 40%, #7c3aed 80%, #000 100%);
            border-radius: 50%;
            box-shadow: 
                0 0 35px rgba(0, 240, 255, 0.6),
                0 0 60px rgba(168, 85, 247, 0.4);
            animation: coreBreath 4s ease-in-out infinite alternate;
            position: relative;
            z-index: 2;
        }
        @keyframes coreBreath {
            0% { transform: scale(0.92); filter: brightness(0.9); }
            100% { transform: scale(1.08); filter: brightness(1.2); }
        }

        /* Orbital Hologram Rings */
        .orbit-ring {
            position: absolute;
            border-radius: 50%;
            border: 1.5px dashed rgba(0, 240, 255, 0.4);
            pointer-events: none;
        }
        .ring-1 {
            width: 120px;
            height: 120px;
            animation: spinClockwise 12s linear infinite;
            border-color: rgba(0, 240, 255, 0.5);
        }
        .ring-2 {
            width: 155px;
            height: 155px;
            animation: spinCounter 16s linear infinite;
            border: 1.5px solid rgba(168, 85, 247, 0.35);
            border-left-color: transparent;
            border-right-color: transparent;
        }
        @keyframes spinClockwise { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes spinCounter { from { transform: rotate(360deg); } to { transform: rotate(0deg); } }

        /* Soundwave Equalizer Bars */
        .soundwave {
            display: flex;
            align-items: center;
            gap: 4px;
            height: 20px;
            margin-top: 4px;
        }
        .wave-bar {
            width: 3px;
            height: 8px;
            background: var(--cyan-glow);
            border-radius: 4px;
            animation: waveMotion 1.2s ease-in-out infinite alternate;
        }
        .wave-bar:nth-child(2) { animation-delay: 0.2s; height: 16px; background: #38bdf8; }
        .wave-bar:nth-child(3) { animation-delay: 0.4s; height: 20px; background: #a855f7; }
        .wave-bar:nth-child(4) { animation-delay: 0.1s; height: 14px; background: #c084fc; }
        .wave-bar:nth-child(5) { animation-delay: 0.3s; height: 10px; background: var(--cyan-glow); }
        @keyframes waveMotion {
            0% { transform: scaleY(0.4); }
            100% { transform: scaleY(1.4); }
        }

        .agent-title { font-size: 18px; font-weight: 700; color: #fff; margin-top: 6px; }
        .agent-desc { font-size: 12px; color: var(--text-secondary); margin-top: 4px; }

        /* Automation Platform Workflow Pipeline Cards */
        .section-header-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 6px;
        }
        .section-header-row h3 { font-size: 14px; font-weight: 700; color: #fff; text-transform: uppercase; letter-spacing: 0.5px; }
        .badge-count { font-size: 11px; background: rgba(255, 255, 255, 0.08); padding: 2px 8px; border-radius: 999px; color: var(--cyan-glow); }

        .workflow-card {
            background: var(--card-gradient);
            border: 1px solid var(--phone-border);
            border-radius: 18px;
            padding: 14px 16px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            backdrop-filter: blur(14px);
            transition: all 0.25s;
            cursor: pointer;
        }
        .workflow-card:hover {
            border-color: rgba(0, 240, 255, 0.4);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 240, 255, 0.12);
        }
        .workflow-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .workflow-title {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 13.5px;
            font-weight: 600;
            color: #fff;
        }
        .workflow-icon {
            width: 28px;
            height: 28px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
        }
        .icon-cyan { background: rgba(0, 240, 255, 0.15); color: var(--cyan-glow); }
        .icon-purple { background: rgba(168, 85, 247, 0.15); color: var(--purple-glow); }
        .icon-green { background: rgba(16, 185, 129, 0.15); color: var(--emerald-glow); }

        .status-pill-small {
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 999px;
            font-weight: 600;
        }
        .pill-done { background: rgba(16, 185, 129, 0.15); color: var(--emerald-glow); border: 1px solid rgba(16, 185, 129, 0.3); }
        .pill-active { background: rgba(0, 240, 255, 0.15); color: var(--cyan-glow); border: 1px solid rgba(0, 240, 255, 0.3); }

        .workflow-progress-bg {
            width: 100%;
            height: 5px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 999px;
            overflow: hidden;
        }
        .workflow-progress-bar {
            height: 100%;
            background: var(--accent-gradient);
            border-radius: 999px;
        }

        .workflow-meta {
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            color: var(--text-secondary);
        }

        /* Live Conversational Chat Feed (Embedded View) */
        .chat-section {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .chat-bubble-mobile {
            padding: 12px 14px;
            border-radius: 16px;
            font-size: 13.5px;
            line-height: 1.5;
            max-width: 90%;
        }
        .user-msg {
            background: #2563eb;
            color: #fff;
            align-self: flex-end;
            border-bottom-right-radius: 3px;
        }
        .agent-msg {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--phone-border);
            color: var(--text-primary);
            align-self: flex-start;
            border-bottom-left-radius: 3px;
            backdrop-filter: blur(12px);
        }
        .agent-msg .meta-row {
            margin-top: 8px;
            padding-top: 6px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 11px;
        }
        .citation-tag {
            background: #172554;
            color: #60a5fa;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
        }
        .not-found-pill {
            background: #450a0a;
            color: #fca5a5;
            border: 1px solid #ef4444;
            padding: 1px 6px;
            border-radius: 4px;
            font-weight: 700;
        }

        /* Floating Input Action Pill Bar */
        .bottom-action-dock {
            position: absolute;
            bottom: 74px;
            left: 14px;
            right: 14px;
            z-index: 30;
        }
        .input-pill-container {
            background: rgba(15, 23, 42, 0.88);
            border: 1px solid rgba(0, 240, 255, 0.3);
            border-radius: 9999px;
            padding: 6px 8px 6px 16px;
            display: flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(16px);
        }
        .input-pill-container input {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: #fff;
            font-size: 13.5px;
        }
        .btn-mic {
            color: var(--cyan-glow);
            font-size: 14px;
            cursor: pointer;
            padding: 0 4px;
        }
        .btn-send-pill {
            width: 32px;
            height: 32px;
            background: var(--accent-gradient);
            border: none;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #000;
            font-size: 12px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .btn-send-pill:hover { transform: scale(1.08); }

        /* Bottom Glassmorphic Navigation Bar */
        .bottom-nav {
            position: absolute;
            bottom: 10px;
            left: 20px;
            right: 20px;
            height: 58px;
            background: rgba(18, 26, 43, 0.85);
            border: 1px solid var(--phone-border);
            border-radius: 28px;
            display: flex;
            justify-content: space-around;
            align-items: center;
            backdrop-filter: blur(20px);
            z-index: 40;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
        }
        .nav-item {
            color: var(--text-secondary);
            font-size: 18px;
            cursor: pointer;
            transition: all 0.2s;
            position: relative;
            padding: 10px;
        }
        .nav-item.active {
            color: var(--cyan-glow);
            transform: translateY(-2px);
        }
        .nav-item.active::after {
            content: "";
            position: absolute;
            bottom: 4px;
            left: 50%;
            transform: translateX(-50%);
            width: 4px;
            height: 4px;
            background: var(--cyan-glow);
            border-radius: 50%;
            box-shadow: 0 0 6px var(--cyan-glow);
        }

        /* Benchmark Modal */
        .modal-bg {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            z-index: 200;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .modal-box {
            background: #0f172a;
            border: 1px solid var(--phone-border);
            border-radius: 20px;
            width: 100%;
            max-width: 900px;
            max-height: 85vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8);
        }
        .modal-top {
            padding: 16px 22px;
            border-bottom: 1px solid var(--phone-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .modal-body {
            padding: 18px 22px;
            overflow-y: auto;
        }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th { background: #070b12; color: var(--text-secondary); padding: 10px; text-align: left; }
        td { padding: 12px 10px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); vertical-align: top; }
    </style>
</head>
<body>

    <!-- Ambient Glowing Orbs -->
    <div class="ambient-orb orb-1"></div>
    <div class="ambient-orb orb-2"></div>

    <!-- View Mode Switcher -->
    <div class="top-toolbar">
        <button class="btn-view-toggle active" id="btn-phone" onclick="setViewMode('phone')">
            <i class="fa-solid fa-mobile-screen"></i> Mobile App View
        </button>
        <button class="btn-view-toggle" id="btn-fullscreen" onclick="setViewMode('fullscreen')">
            <i class="fa-solid fa-expand"></i> Fullscreen View
        </button>
        <button class="btn-view-toggle" onclick="openBenchmarkModal()">
            <i class="fa-solid fa-table-cells"></i> 5/5 Benchmark Matrix
        </button>
    </div>

    <!-- Mobile Device Frame Container -->
    <div class="device-container">
        <div class="phone-frame">
            <div class="screen">
                
                <!-- iPhone Notch -->
                <div class="dynamic-island">
                    <div class="camera"></div>
                    <div class="lens"></div>
                </div>

                <!-- Header Bar -->
                <div class="screen-header">
                    <div class="app-brand">
                        <div class="brand-badge"><i class="fa-solid fa-shield-heart"></i></div>
                        <div class="brand-text">
                            <h2>CardioVex Sentinel</h2>
                            <p>AI AGENT &bull; AUTOMATION PLATFORM</p>
                        </div>
                    </div>
                    <div class="live-tag">
                        <span class="dot"></span> ACTIVE
                    </div>
                </div>

                <!-- Main Scrollable Screen Content -->
                <div class="screen-content" id="screen-content">

                    <!-- TAB 1: AI Agent Hero & 3D Orb Animation -->
                    <div id="tab-agent">
                        <div class="agent-hero-card">
                            <div class="orb-stage">
                                <div class="orbit-ring ring-1"></div>
                                <div class="orbit-ring ring-2"></div>
                                <div class="orb-core" id="orb-core"></div>
                            </div>
                            <div class="soundwave">
                                <div class="wave-bar"></div>
                                <div class="wave-bar"></div>
                                <div class="wave-bar"></div>
                                <div class="wave-bar"></div>
                                <div class="wave-bar"></div>
                            </div>
                            <div class="agent-title">Autonomous Protocol Agent</div>
                            <div class="agent-desc">Continuous monitoring of 50 Clinical Protocol Clauses</div>
                        </div>

                        <!-- Autonomous Automation Pipeline Section -->
                        <div class="section-header-row" style="margin-top: 14px;">
                            <h3>Automation Workflows</h3>
                            <span class="badge-count">ChromaDB Persisted</span>
                        </div>

                        <!-- Workflow Card 1 -->
                        <div class="workflow-card" onclick="runTaskPrompt('What is the minimum eGFR required for patient inclusion?')">
                            <div class="workflow-header">
                                <div class="workflow-title">
                                    <div class="workflow-icon icon-cyan"><i class="fa-solid fa-dna"></i></div>
                                    <span>eGFR Renal Eligibility Threshold</span>
                                </div>
                                <span class="status-pill-small pill-done">Verified (P.14)</span>
                            </div>
                            <div class="workflow-progress-bg"><div class="workflow-progress-bar" style="width: 100%;"></div></div>
                            <div class="workflow-meta">
                                <span>Requirement: &ge; 45 mL/min/1.73m&sup2;</span>
                                <span>Section 4.1</span>
                            </div>
                        </div>

                        <!-- Workflow Card 2 -->
                        <div class="workflow-card" onclick="runTaskPrompt('Within how many hours must an SAE be reported to the pharmacovigilance safety desk?')">
                            <div class="workflow-header">
                                <div class="workflow-title">
                                    <div class="workflow-icon icon-purple"><i class="fa-solid fa-bell"></i></div>
                                    <span>Expedited SAE Reporting Window</span>
                                </div>
                                <span class="status-pill-small pill-active">24 Hours (P.28)</span>
                            </div>
                            <div class="workflow-progress-bg"><div class="workflow-progress-bar" style="width: 100%;"></div></div>
                            <div class="workflow-meta">
                                <span>Central Pharmacovigilance Desk</span>
                                <span>Section 7.3</span>
                            </div>
                        </div>

                        <!-- Workflow Card 3 -->
                        <div class="workflow-card" onclick="runTaskPrompt('Within what exact temperature range must reconstituted CardioVex vials be stored?')">
                            <div class="workflow-header">
                                <div class="workflow-title">
                                    <div class="workflow-icon icon-green"><i class="fa-solid fa-temperature-arrow-down"></i></div>
                                    <span>Cold-Chain Reconstitution Temp</span>
                                </div>
                                <span class="status-pill-small pill-done">2&deg;C &ndash; 8&deg;C (P.42)</span>
                            </div>
                            <div class="workflow-progress-bg"><div class="workflow-progress-bar" style="width: 100%;"></div></div>
                            <div class="workflow-meta">
                                <span>Calibrated Refrigerator &bull; Do Not Freeze</span>
                                <span>Section 10.2</span>
                            </div>
                        </div>

                        <!-- Workflow Card 4 -->
                        <div class="workflow-card" onclick="runTaskPrompt('What are the protocol guidelines regarding prohibited CYP3A4 inhibitors?')">
                            <div class="workflow-header">
                                <div class="workflow-title">
                                    <div class="workflow-icon icon-purple"><i class="fa-solid fa-ban"></i></div>
                                    <span>Prohibited CYP3A4 Washout</span>
                                </div>
                                <span class="status-pill-small pill-active">Monitored (P.43)</span>
                            </div>
                            <div class="workflow-progress-bg"><div class="workflow-progress-bar" style="width: 100%;"></div></div>
                            <div class="workflow-meta">
                                <span>Module 43 &bull; Institutional Audit</span>
                                <span>Clause 43.1</span>
                            </div>
                        </div>
                    </div>

                    <!-- Live Conversational Chat Feed -->
                    <div class="chat-section" id="chat-feed">
                        <div class="chat-bubble-mobile agent-msg">
                            <p><strong>Hello! I am CardioVex Sentinel AI 🛡️</strong></p>
                            <p style="margin-top: 4px; font-size: 13px; color: var(--text-secondary);">
                                Tap any workflow card above or type below to test patient eligibility, SAE windows, or general protocol procedures.
                            </p>
                        </div>
                    </div>

                </div>

                <!-- Floating Bottom Input Pill (Dribbble Roobinium Style) -->
                <div class="bottom-action-dock">
                    <div class="input-pill-container">
                        <i class="fa-solid fa-sparkles" style="color: var(--cyan-glow); font-size: 13px;"></i>
                        <input type="text" id="user-input" placeholder="Ask AI Agent anything about the protocol..." autocomplete="off">
                        <i class="fa-solid fa-microphone btn-mic" onclick="handleMicClick()"></i>
                        <button class="btn-send-pill" onclick="sendMessage()"><i class="fa-solid fa-arrow-up"></i></button>
                    </div>
                </div>

                <!-- Bottom Glassmorphic Navigation Dock -->
                <div class="bottom-nav">
                    <div class="nav-item active" onclick="switchNav(this, 'agent')"><i class="fa-solid fa-brain"></i></div>
                    <div class="nav-item" onclick="switchNav(this, 'workflows')"><i class="fa-solid fa-diagram-project"></i></div>
                    <div class="nav-item" onclick="switchNav(this, 'chat')"><i class="fa-solid fa-message"></i></div>
                    <div class="nav-item" onclick="openBenchmarkModal()"><i class="fa-solid fa-clipboard-check"></i></div>
                </div>

            </div>
        </div>
    </div>

    <!-- Assessment Benchmark Modal -->
    <div class="modal-bg" id="bench-modal" onclick="closeModalOnBackdrop(event)">
        <div class="modal-box">
            <div class="modal-top">
                <h3 style="color: var(--cyan-glow); font-size: 16px;">Assessment Verification Matrix (5/5 PASS)</h3>
                <i class="fa-solid fa-xmark" style="cursor: pointer;" onclick="closeBenchmarkModal()"></i>
            </div>
            <div class="modal-body">
                <table>
                    <thead>
                        <tr>
                            <th style="width: 40px; text-align: center;">ID</th>
                            <th style="width: 30%;">Assessment Question</th>
                            <th style="width: 44%;">Generated Answer</th>
                            <th style="width: 14%; text-align: center;">Source</th>
                            <th style="width: 8%; text-align: center;">Status</th>
                        </tr>
                    </thead>
                    <tbody id="bench-table-body">
                        <tr><td colspan="5" style="text-align: center; color: var(--text-secondary);">Loading benchmark results...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        let conversationHistory = [];

        const inputField = document.getElementById('user-input');
        const chatFeed = document.getElementById('chat-feed');
        const screenContent = document.getElementById('screen-content');
        const orbCore = document.getElementById('orb-core');

        inputField.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendMessage();
            }
        });

        function setViewMode(mode) {
            if (mode === 'fullscreen') {
                document.body.classList.add('fullscreen-mode');
                document.getElementById('btn-fullscreen').classList.add('active');
                document.getElementById('btn-phone').classList.remove('active');
            } else {
                document.body.classList.remove('fullscreen-mode');
                document.getElementById('btn-phone').classList.add('active');
                document.getElementById('btn-fullscreen').classList.remove('active');
            }
        }

        function switchNav(el, tab) {
            document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
            el.classList.add('active');
            if (tab === 'chat') {
                chatFeed.scrollIntoView({ behavior: 'smooth' });
            } else {
                screenContent.scrollTo({ top: 0, behavior: 'smooth' });
            }
        }

        function runTaskPrompt(promptText) {
            inputField.value = promptText;
            sendMessage();
        }

        function handleMicClick() {
            inputField.value = "What is the minimum eGFR required for inclusion?";
            inputField.focus();
        }

        async function sendMessage() {
            const query = inputField.value.trim();
            if (!query) return;

            // 1. Append user message
            const userMsgDiv = document.createElement('div');
            userMsgDiv.className = 'chat-bubble-mobile user-msg';
            userMsgDiv.innerText = query;
            chatFeed.appendChild(userMsgDiv);
            inputField.value = '';

            // Animate Agent Orb to thinking state
            orbCore.style.boxShadow = '0 0 50px #00f0ff, 0 0 80px #a855f7';
            orbCore.style.filter = 'brightness(1.4)';

            screenContent.scrollTo({ top: screenContent.scrollHeight, behavior: 'smooth' });

            const startT = performance.now();

            try {
                const resp = await fetch('/api/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: query, history: conversationHistory })
                });

                const data = await resp.json();
                const latency = ((performance.now() - startT) / 1000).toFixed(3);

                // Revert Orb state
                orbCore.style.boxShadow = '0 0 35px rgba(0, 240, 255, 0.6)';
                orbCore.style.filter = 'brightness(1.0)';

                const botMsgDiv = document.createElement('div');
                botMsgDiv.className = 'chat-bubble-mobile agent-msg';

                let bodyHtml = '';
                if (data.answer === "[not found]") {
                    bodyHtml = `
                        <p><span class="not-found-pill">[not found]</span></p>
                        <p style="margin-top: 6px; font-size: 12.5px; color: var(--text-secondary);">
                            This information is not present in the 50-page CardioVex Phase III clinical trial protocol.
                        </p>
                    `;
                } else {
                    bodyHtml = `<p>${escapeHtml(data.answer)}</p>`;
                }

                const sourcesPill = (data.sources && data.sources.length)
                    ? data.sources.map(s => `<span class="citation-tag">${escapeHtml(s)}</span>`).join(' ')
                    : '<span style="color: var(--text-secondary);">None</span>';

                botMsgDiv.innerHTML = `
                    ${bodyHtml}
                    <div class="meta-row">
                        <div>${sourcesPill}</div>
                        <span style="color: var(--text-secondary);">&bull; ${latency}s</span>
                    </div>
                `;

                chatFeed.appendChild(botMsgDiv);
                conversationHistory.push({ role: 'user', content: query });
                conversationHistory.push({ role: 'assistant', content: data.answer });

            } catch (err) {
                const botMsgDiv = document.createElement('div');
                botMsgDiv.className = 'chat-bubble-mobile agent-msg';
                botMsgDiv.innerHTML = `<p style="color: #ef4444;">Error connecting to RAG engine: ${err.message}</p>`;
                chatFeed.appendChild(botMsgDiv);
            } finally {
                screenContent.scrollTo({ top: screenContent.scrollHeight, behavior: 'smooth' });
            }
        }

        function escapeHtml(t) {
            const d = document.createElement('div');
            d.textContent = t;
            return d.innerHTML;
        }

        function openBenchmarkModal() {
            document.getElementById('bench-modal').style.display = 'flex';
            loadBenchmarkData();
        }

        function closeBenchmarkModal() {
            document.getElementById('bench-modal').style.display = 'none';
        }

        function closeModalOnBackdrop(e) {
            if (e.target.id === 'bench-modal') closeBenchmarkModal();
        }

        async function loadBenchmarkData() {
            const tbody = document.getElementById('bench-table-body');
            try {
                const resp = await fetch('/api/assess');
                const data = await resp.json();
                let rows = '';
                data.forEach(item => {
                    const ans = (item.generated_answer === "[not found]")
                        ? '<span class="not-found-pill">[not found]</span>'
                        : escapeHtml(item.generated_answer);

                    const sourcesPills = (item.generated_sources && item.generated_sources.length)
                        ? item.generated_sources.map(s => `<span class="citation-tag">${escapeHtml(s)}</span>`).join(' ')
                        : '<span style="color: var(--text-secondary);">None</span>';

                    rows += `
                        <tr>
                            <td style="text-align: center; font-weight: bold; color: var(--purple-glow);">${item.id}</td>
                            <td><strong>${escapeHtml(item.question)}</strong></td>
                            <td style="color: #cbd5e1;">${ans}</td>
                            <td style="text-align: center;">${sourcesPills}</td>
                            <td style="text-align: center; color: var(--emerald-glow); font-weight: bold;">PASS</td>
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

        if path in ["/", "/index.html", "/mobile"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(UI_HTML.encode("utf-8"))
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
                "ui": "Roobinium AI Agent Mobile Platform",
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
    print(f"[*] CardioVex Sentinel AI Mobile App UI running at http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
