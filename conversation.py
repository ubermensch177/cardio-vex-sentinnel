"""
Conversation Management and Contextual Query Rewriting for CardioVex Sentinel AI.
Maintains multi-turn conversation history and resolves referential follow-up questions
into standalone semantic search queries.
"""

import re
from typing import Dict, List, Optional


class ConversationManager:
    """Manages chat history and session memory for conversational RAG."""

    def __init__(self):
        self.history: List[Dict[str, str]] = []

    def add_message(self, role: str, content: str):
        """Appends a message turn (role: 'user' or 'assistant')."""
        self.history.append({"role": role, "content": content})

    def get_history(self) -> List[Dict[str, str]]:
        """Returns the complete conversation history."""
        return self.history

    def get_recent_turns(self, n: int = 4) -> List[Dict[str, str]]:
        """Returns the most recent n turns."""
        return self.history[-n:] if len(self.history) > n else self.history

    def clear(self):
        """Resets the conversation history."""
        self.history = []


# Domain nomenclature mapping for robust semantic expansion
CLINICAL_TOPIC_EXPANSIONS = {
    "sae": "Serious Adverse Event (SAE) expedited reporting timeline and Pharmacovigilance Safety Desk",
    "serious adverse event": "Serious Adverse Event (SAE) expedited reporting timeline and Pharmacovigilance Safety Desk",
    "safety desk": "Pharmacovigilance Safety Desk Serious Adverse Event (SAE) reporting window",
    "egfr": "estimated Glomerular Filtration Rate (eGFR) renal function threshold patient inclusion criteria",
    "glomerular": "estimated Glomerular Filtration Rate (eGFR) baseline renal threshold patient inclusion criteria",
    "renal": "estimated Glomerular Filtration Rate (eGFR) renal function inclusion and exclusion criteria",
    "temperature": "reconstituted CardioVex vial storage temperature range degrees Celsius cold-chain",
    "reconstitut": "reconstituted CardioVex vial storage temperature range degrees Celsius cold-chain",
    "vial": "reconstituted CardioVex vial storage temperature range degrees Celsius cold-chain",
    "cold-chain": "investigational product cold-chain storage requirements refrigerator temperature logging",
    "cyp3a4": "concomitant medication washout schedules and prohibited CYP3A4 inhibitors",
    "washout": "concomitant medication washout schedules and prohibited CYP3A4 inhibitors",
    "informed consent": "informed consent documentation and Good Clinical Practice (ICH-GCP) audits",
    "gcp": "Good Clinical Practice (ICH-GCP) audits and informed consent documentation",
    "echocardiograph": "baseline echocardiography biomarkers and central laboratory blood panels",
    "blood panel": "central laboratory blood panels and baseline echocardiography biomarkers",
    "dsmb": "statistical power calculations, Kaplan-Meier endpoints, and DSMB charter",
    "kaplan-meier": "statistical power calculations, Kaplan-Meier endpoints, and DSMB charter",
    "endpoint": "Kaplan-Meier endpoints and statistical power calculations",
    "dose": "CardioVex study drug dosing, administration, and pharmacokinetics",
    "administration": "CardioVex administration, dosing, and cold-chain storage"
}


def rewrite_query_with_context(query: str, history: Optional[List[Dict[str, str]]] = None) -> str:
    """
    Contextual Query Rewriter.
    Resolves pronouns, short references, and follow-up inquiries (e.g., 'Why?', 'What happens if they fail?',
    'What about SAEs?', 'Summarize it', 'Explain in simple terms') using preceding dialogue turns.
    """
    if not query or not query.strip():
        return ""

    q_clean = query.strip()
    q_lower = q_clean.lower()

    # Direct clinical topic expansion check
    for key, expansion in CLINICAL_TOPIC_EXPANSIONS.items():
        if re.search(r"\b" + re.escape(key) + r"\b", q_lower):
            # If query is short or referential, expand with topic
            if len(q_clean.split()) <= 8 or any(w in q_lower for w in ["what about", "how about", "hours", "timeline", "reporting", "temp"]):
                return f"{expansion} {q_clean}"

    if not history:
        return q_clean

    referential_keywords = [
        "why", "what about", "how about", "what happens if", "summarize", "explain this",
        "what are the other", "what else", "compare", "in simple terms", "tell me more",
        "is that required", "why is that", "who reports", "what if", "does it", "criteria",
        "what happens next", "hours", "timeline", "when"
    ]

    is_referential = (len(q_clean.split()) <= 7) or any(k in q_lower for k in referential_keywords)

    if not is_referential:
        return q_clean

    # Extract previous user question and assistant answer
    last_user_query = None
    last_bot_answer = None

    for msg in reversed(history):
        if msg.get("role") == "user" and last_user_query is None:
            last_user_query = msg.get("content", "")
        elif msg.get("role") == "assistant" and last_bot_answer is None:
            last_bot_answer = msg.get("content", "")

    if not last_user_query:
        return q_clean

    # Clean the previous user question
    prev_clean = re.sub(
        r"^(what|who|when|where|why|how|is|are|does|do|can|could|should|would)\s+(is|are|the|a|an)?\s*",
        "", last_user_query, flags=re.IGNORECASE
    ).strip(" ?.")

    # Match previous subject with clinical expansions if possible
    prev_expansion = prev_clean
    for key, expansion in CLINICAL_TOPIC_EXPANSIONS.items():
        if re.search(r"\b" + re.escape(key) + r"\b", prev_clean.lower()):
            prev_expansion = expansion
            break

    # Contextual expansion
    if "fail" in q_lower:
        return f"{prev_expansion} patient failure protocol exclusion criteria consequences strictly excluded"
    elif "why" in q_lower:
        return f"{prev_expansion} clinical rationale mechanism objective protocol requirements"
    elif "other criteria" in q_lower or "exclusion" in q_lower:
        return f"{prev_expansion} patient exclusion eligibility criteria heart failure"
    elif "summarize" in q_lower:
        return f"{prev_expansion} comprehensive overview protocol procedures"
    elif "simple" in q_lower or "detail" in q_lower:
        return f"{prev_expansion} complete clinical parameters"
    elif "hours" in q_lower or "timeline" in q_lower or "reporting" in q_lower:
        return f"{prev_expansion} reporting timeline hours requirements"
    elif "what about" in q_lower or "how about" in q_lower:
        sub = re.sub(r"^(what about|how about)\s+", "", q_lower).strip(" ?.")
        return f"CardioVex Phase III trial {sub} protocol guidelines"

    return f"{prev_expansion} {q_clean}"
