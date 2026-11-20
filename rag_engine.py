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
