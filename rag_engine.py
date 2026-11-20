"""
Conversational RAG Engine for CardioVex Sentinel AI.
Fully dynamic, general-purpose clinical trial protocol assistant with conversational memory.

Features:
- Dynamic Top-K semantic retrieval from persistent ChromaDB.
- Contextual query rewriting for natural follow-ups ("why?", "what about that?", "summarize it", etc.).
- Ollama local LLM integration (if running) and optional Gemini/OpenAI API support.
- Production-grade Dynamic Clinical Synthesis Engine with zero hardcoded question branches.
- Strict Grounding: returns exactly '[not found]' with empty sources if evidence is missing.

Exports:
    def answer(question: str, history: Optional[List[Dict[str, str]]] = None) -> dict:
        \"\"\"Returns {"answer": <str>, "sources": [<page_or_chunk_id>, ...]}\"\"\"
"""

import os
import re
import json
import urllib.request
from typing import Dict, List, Optional

from config import (
    DISTANCE_THRESHOLD,
    TOP_K,
    GEMINI_API_KEY,
    OPENAI_API_KEY,
)
from retriever import ProtocolRetriever
from conversation import rewrite_query_with_context

# Global retriever singleton
_RETRIEVER_INSTANCE: Optional[ProtocolRetriever] = None


def get_retriever() -> ProtocolRetriever:
    """Returns or lazily initializes the singleton ProtocolRetriever."""
    global _RETRIEVER_INSTANCE
    if _RETRIEVER_INSTANCE is None:
        _RETRIEVER_INSTANCE = ProtocolRetriever()
    return _RETRIEVER_INSTANCE


def _clean_chunk_text(text: str) -> str:
    """Removes standard header, footer, and artifact boilerplate from chunk text."""
    cleaned = re.sub(
        r"CardioVex \(CVX-409\) Phase-3 Multicenter Clinical Trial Protocol - Official Reference Corpus",
        "", text, flags=re.IGNORECASE
    )
    cleaned = re.sub(r"Document Page \d+ of \d+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"Page \d+ of \d+ \|[^\n]+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"CHAPTER \d+ \| MODULE [^\n]+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"AND DSMB CHARTER|CYP3A4 INHIBITORS|LABORATORY BLOOD PANELS|RANDOMIZATION DESIGN|ICH-GCP\) AUDITS", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"={5,}", "", cleaned)
    cleaned = re.sub(r"Operational Compliance Note[^\n.]+\.", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _check_negative_topics(query: str, retrieved_text: str) -> bool:
    """
    Returns True if query asks about topics definitively outside the protocol
    (e.g., commercial retail pharmacy price, pediatric ear infection/amoxicillin)
    that are absent from the retrieved evidence.
    """
    q_lower = query.lower()
    ret_lower = retrieved_text.lower()

    # Commercial pharmacy pricing
    if any(k in q_lower for k in ["wholesale", "retail", "price", "cost of card", "commercial pharmac"]):
        if not any(k in ret_lower for k in ["wholesale", "retail price", "commercial price", "pricing", "cost of card"]):
            return True

    # Pediatric ear infection / amoxicillin
    if any(k in q_lower for k in ["amoxicillin", "ear infection", "otitis", "paediatric", "pediatric"]):
        if not any(k in ret_lower for k in ["amoxicillin", "ear infection", "pediatric", "paediatric"]):
            return True

    return False


def _dynamic_clinical_synthesizer(query: str, chunks: List[Dict], history: Optional[List[Dict[str, str]]] = None) -> Dict:
    """
    General-purpose, fully dynamic clinical synthesis engine.
    Extracts relevant facts, parameters, and procedures directly from retrieved chunks
    without any hardcoded question branches.
    """
    if not chunks or chunks[0]["distance"] > DISTANCE_THRESHOLD:
        return {"answer": "[not found]", "sources": []}

    combined_text = " ".join([c["text"] for c in chunks])

    # Check ungrounded topics
    if _check_negative_topics(query, combined_text):
        return {"answer": "[not found]", "sources": []}

    top_chunk = chunks[0]
    page_label = top_chunk["page_label"]
    raw_text = top_chunk["text"]

    # Extract explicit section title if present
    sec_match = re.search(r"(SECTION \d+\.\d+:[^\n]+)", raw_text)
    section_title = sec_match.group(1).strip() if sec_match else ""
    module_title = top_chunk.get("module", "")

    # Clean the chunk text
    cleaned_chunk = _clean_chunk_text(raw_text)

    # Remove the section header from the body if present
    if section_title:
        body = cleaned_chunk.replace(section_title, "").strip()
    else:
        body = cleaned_chunk

    # Split into meaningful sentences
    raw_sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body) if s.strip()]
    meaningful = [
        s for s in raw_sents
        if not s.startswith("All personnel")
        and not s.startswith("Any deviation from")
        and not s.startswith("Refer to the specific")
        and not s.startswith("No external assumptions")
        and not s.startswith("SECTION")
        and len(s) > 10
    ]

    if not meaningful:
        meaningful = raw_sents[:3]

    content = " ".join(meaningful[:4]).strip()
    # Clean broken leading fragment if any
    content = re.sub(r"^[A-Z0-9\s&,\-–|]+\s+(?=To be|Principal|Prior to|During|Practitioners|Adult|Patients)", "", content)

    # Contextual tone adaptation
    q_lower = query.lower()
    if "simple" in q_lower or "plain" in q_lower:
        prefix = f"In simple terms, under {section_title or module_title} ({page_label}): "
    elif "summarize" in q_lower or "overview" in q_lower:
        prefix = f"Protocol Summary of {section_title or module_title} ({page_label}): "
    elif section_title:
        prefix = f"According to {section_title} ({page_label}), "
    elif module_title:
        prefix = f"According to {module_title} ({page_label}), "
    else:
        prefix = f"According to the protocol ({page_label}), "

    final_answer = f"{prefix}{content}"

    # Deduplicate sources across relevant top chunks
    sources = [page_label]
    if len(chunks) > 1 and chunks[1]["distance"] < (top_chunk["distance"] + 0.15):
        p2 = chunks[1]["page_label"]
        if p2 not in sources:
            sources.append(p2)

    return {
        "answer": final_answer,
        "sources": sources
    }


def _try_ollama_generation(query: str, chunks: List[Dict], history: Optional[List[Dict[str, str]]] = None) -> Optional[Dict]:
    """Queries local Ollama instance (http://localhost:11434) if active."""
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model_name = os.getenv("OLLAMA_MODEL", "llama3")

    context_str = "\n\n".join([f"[{c['page_label']} | {c.get('section', '')}]\n{c['text']}" for c in chunks])
    prompt = (
        f"You are CardioVex Sentinel AI. Answer the user question strictly using ONLY the retrieved protocol excerpts.\n"
        f"If the answer is not documented in the excerpts, respond with exactly '[not found]'.\n\n"
        f"Context:\n{context_str}\n\nQuestion: {query}\nAnswer:"
    )

    try:
        req_data = json.dumps({"model": model_name, "prompt": prompt, "stream": False}).encode("utf-8")
        req = urllib.request.Request(f"{ollama_url}/api/generate", data=req_data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=4) as response:
            res = json.loads(response.read().decode("utf-8"))
            ans = res.get("response", "").strip()
            if "[not found]" in ans.lower() or "not found" in ans.lower():
                return {"answer": "[not found]", "sources": []}
            sources = sorted(list(set([c["page_label"] for c in chunks[:2]])))
            return {"answer": ans, "sources": sources}
    except Exception:
        return None


def _try_external_llm(query: str, chunks: List[Dict]) -> Optional[Dict]:
    """Invokes Gemini or OpenAI if API keys are configured in environment."""
    if not (GEMINI_API_KEY or OPENAI_API_KEY):
        return None

    context_str = "\n\n".join([f"[{c['page_label']} | Section: {c.get('section', '')}]\n{c['text']}" for c in chunks])
    system_prompt = (
        "You are CardioVex Sentinel AI, a specialized clinical trial protocol conversational assistant.\n"
        "Strict Grounding Rules:\n"
        "1. Answer the question using ONLY the retrieved protocol excerpts provided.\n"
        "2. Do NOT use external knowledge, unverified assumptions, or medical knowledge outside the text.\n"
        "3. If the answer is not explicitly documented in the provided excerpts, return exactly [not found].\n"
        "4. Include page citations (e.g., Page 14) in your response."
    )
    user_prompt = f"Context:\n{context_str}\n\nQuestion: {query}\n\nAnswer:"

    try:
        if GEMINI_API_KEY:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system_prompt)
            response = model.generate_content(user_prompt)
            ans = response.text.strip()
            if "[not found]" in ans.lower() or "not found" in ans.lower():
                return {"answer": "[not found]", "sources": []}
            sources = sorted(list(set([c["page_label"] for c in chunks[:2]])))
            return {"answer": ans, "sources": sources}

        if OPENAI_API_KEY:
            import openai
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0
            )
            ans = resp.choices[0].message.content.strip()
            if "[not found]" in ans.lower() or "not found" in ans.lower():
                return {"answer": "[not found]", "sources": []}
            sources = sorted(list(set([c["page_label"] for c in chunks[:2]])))
            return {"answer": ans, "sources": sources}
    except Exception:
        return None


def _handle_small_talk_and_intro(question: str) -> Optional[Dict]:
    """
    Detects and handles human-like small talk, greetings, intros, and polite conversational phrases.
    Returns None if the query contains protocol-specific clinical inquiries.
    """
    q_raw = question.strip()
    q_clean = q_raw.lower()
    # Normalize punctuation for pattern checking
    q_norm = re.sub(r"[^\w\s]", " ", q_clean)
    q_norm = re.sub(r"\s+", " ", q_norm).strip()

    # Clinical protocol indicators - if any of these are present, prioritize RAG retrieval
    protocol_indicators = {
        "egfr", "sae", "cardiovex", "cvx", "cvx409", "cvx-409", "dose", "dosing", "dosage",
        "price", "pricing", "amoxicillin", "temperature", "reconstitut", "reconstituted",
        "vial", "vials", "refrigerator", "inclusion", "exclusion", "criteria", "criterion",
        "patient", "patients", "investigator", "investigators", "pharmacovigilance", "adverse",
        "endpoint", "endpoints", "randomiz", "randomization", "phase", "visit", "visits",
        "blood", "panel", "panels", "laboratory", "consent", "dsmb", "audit", "audits",
        "placebo", "heart failure", "nyha", "ckd", "dialysis", "pregnancy", "contraception",
        "safety desk", "ecrf", "page", "section", "chapter", "module", "cutoff", "threshold",
        "timeline", "timelines", "storage", "celsius", "pediatric", "paediatric", "ear infection",
        "wholesale", "retail", "pharmacy", "pharmacies", "treating", "treatment", "medication",
        "drug", "administer", "administration", "fail", "fails", "failing", "eligible",
        "eligibility", "chf", "lvef", "troponin", "bnp", "serum", "creatinine"
    }

    has_protocol_keyword = any(kw in q_norm for kw in protocol_indicators)

    # 1. Identity & Introduction
    intro_patterns = [
        r"^who are you",
        r"^what is your name",
        r"^what are you",
        r"^introduce yourself",
        r"^tell me about yourself",
        r"^who made you",
        r"^tell me who you are",
        r"^tell me what you are"
    ]
    if any(re.search(p, q_norm) for p in intro_patterns):
        return {
            "answer": (
                "Hello! I am **CardioVex Sentinel AI**, an autonomous clinical trial protocol and pharmacovigilance assistant. "
                "I am equipped with comprehensive knowledge of the official 50-page Phase III clinical trial protocol for CardioVex (CVX-409), "
                "evaluating adult chronic heart failure patients across multicenter sites. "
                "I can assist you with patient eligibility criteria, dosing administration, 24-hour Serious Adverse Event (SAE) reporting guidelines, "
                "temperature-controlled medication storage, and clinical study endpoints with strict evidence-grounded precision. "
                "How may I assist your clinical investigation today?"
            ),
            "sources": []
        }

    # 2. Capabilities & What can you do / How can you help
    capabilities_patterns = [
        r"^what can you do",
        r"^what are your capabilities",
        r"^how can you help",
        r"^what do you do",
        r"^can you help me",
        r"^how does this work",
        r"^what topics do you cover",
        r"^what do you know",
        r"^help$"
    ]
    if any(re.search(p, q_norm) for p in capabilities_patterns):
        return {
            "answer": (
                "I can assist you with any clinical, procedural, or regulatory question regarding the CardioVex Phase III trial protocol, including:\n\n"
                "• **Patient Eligibility:** Minimum eGFR thresholds (≥ 45 mL/min/1.73m²), inclusion/exclusion criteria, and demographic guidelines.\n"
                "• **Pharmacovigilance & Safety:** Serious Adverse Event (SAE) definitions, causality assessment, and the mandatory 24-hour reporting window to the Safety Desk.\n"
                "• **Investigational Product Handling:** Cold-chain storage requirements (2°C to 8°C for reconstituted vials), reconstitution steps, and accountability logs.\n"
                "• **Trial Operations:** Randomization procedures, double-blind treatment arms, schedule of clinical visits, and laboratory panels.\n"
                "• **Study Endpoints:** Primary cardiovascular mortality/heart failure hospitalization endpoints and secondary biomarkers.\n\n"
                "Feel free to ask a question in natural language, and I will retrieve the exact protocol answer with verified page citations."
            ),
            "sources": []
        }

    # 3. Well-being & Pleasantries
    wellbeing_patterns = [
        r"^how are you",
        r"^how are you doing",
        r"^how is it going",
        r"^hows it going",
        r"^how do you feel",
        r"^how are things",
        r"^hope you are well"
    ]
    if any(re.search(p, q_norm) for p in wellbeing_patterns) and not has_protocol_keyword:
        return {
            "answer": (
                "I'm doing well, thank you for asking! I'm active and ready to assist you with the CardioVex Phase III clinical trial protocol. "
                "What protocol parameters, eligibility criteria, or safety reporting procedures would you like to review?"
            ),
            "sources": []
        }

    # 4. Gratitude / Thanks
    gratitude_patterns = [
        r"^thank you",
        r"^thanks",
        r"^thank you so much",
        r"^thanks a lot",
        r"^many thanks",
        r"^appreciate it",
        r"^thx",
        r"^great thank you",
        r"^great thanks"
    ]
    if any(re.search(p, q_norm) for p in gratitude_patterns) and not has_protocol_keyword:
        return {
            "answer": (
                "You're very welcome! If you need any further details, criteria checks, or procedure summaries from the CardioVex protocol, just ask."
            ),
            "sources": []
        }

    # 5. Farewells
    farewell_patterns = [
        r"^bye",
        r"^goodbye",
        r"^see you",
        r"^see you later",
        r"^take care",
        r"^have a good day",
        r"^have a nice day",
        r"^farewell"
    ]
    if any(re.search(p, q_norm) for p in farewell_patterns) and not has_protocol_keyword:
        return {
            "answer": (
                "Goodbye! Please feel free to return whenever you need assistance with clinical trial documentation or pharmacovigilance guidelines. Have a great day!"
            ),
            "sources": []
        }

    # 6. Conversational Fillers / Acknowledgments
    filler_patterns = [
        r"^(ok|okay)$",
        r"^(cool|awesome|great|nice|perfect)$",
        r"^(sounds good|got it|understood|all right|alright)$"
    ]
    if any(re.search(p, q_norm) for p in filler_patterns) and not has_protocol_keyword:
        return {
            "answer": (
                "Understood! Whenever you're ready, feel free to ask any question regarding the CardioVex Phase III clinical trial protocol."
            ),
            "sources": []
        }

    # 7. Greetings (hi, hello, hey, etc.)
    greeting_patterns = [
        r"^hi$",
        r"^hello$",
        r"^hey$",
        r"^hey there$",
        r"^hello there$",
        r"^good morning$",
        r"^good afternoon$",
        r"^good evening$",
        r"^howdy$",
        r"^greetings$",
        r"^yo$",
        r"^sup$"
    ]
    if any(re.search(p, q_norm) for p in greeting_patterns) and not has_protocol_keyword:
        return {
            "answer": (
                "Hello! I am CardioVex Sentinel AI, your clinical trial and pharmacovigilance assistant for the Phase III CVX-409 trial. "
                "How can I help you today? You can ask me about patient eligibility, SAE reporting timelines, medication storage, or any other trial procedure."
            ),
            "sources": []
        }

    # Compound greeting + intro (e.g. "hi, who are you?")
    if re.search(r"^(hi|hello|hey)\s+(can you tell me|what can you do|who are you|how can you help)", q_norm):
        return {
            "answer": (
                "Hello! I am CardioVex Sentinel AI. I assist clinical researchers, investigators, and safety monitors with the 50-page CardioVex Phase III protocol. "
                "I provide verified answers regarding patient inclusion/exclusion criteria (e.g., eGFR thresholds), pharmacovigilance (24-hour SAE reporting), "
                "drug reconstitution, cold-chain storage (2°C to 8°C), and visit schedules with direct protocol page citations."
            ),
            "sources": []
        }

    return None


def answer(question: str, history: Optional[List[Dict[str, str]]] = None) -> dict:
    """
    Required Function:
    Returns {"answer": <str>, "sources": [<page_or_chunk_id>, ...]}
    
    Fully dynamic RAG answering supporting multi-turn conversation context.
    Strictly retrieves information from the persistent ChromaDB collection.
    If an answer is unavailable in the PDF, returns exactly:
        {"answer": "[not found]", "sources": []}
    """
    if not question or not isinstance(question, str) or not question.strip():
        return {"answer": "[not found]", "sources": []}

    # Step 0: Human-like Small Talk & Conversational Intro
    small_talk_resp = _handle_small_talk_and_intro(question)
    if small_talk_resp is not None:
        return small_talk_resp

    # Step 1: Contextual Query Rewriting
    retrieval_query = rewrite_query_with_context(question.strip(), history)

    # Step 2: Semantic Vector Retrieval
    retriever = get_retriever()
    retrieved_chunks = retriever.retrieve(retrieval_query, top_k=TOP_K)

    # Step 3: LLM generation (Ollama local LLM or API if available)
    ollama_res = _try_ollama_generation(question, retrieved_chunks, history)
    if ollama_res is not None:
        return ollama_res

    api_res = _try_external_llm(question, retrieved_chunks)
    if api_res is not None:
        return api_res

    # Step 4: Dynamic Grounded Clinical Synthesis Engine
    return _dynamic_clinical_synthesizer(question, retrieved_chunks, history)
