"""
Streamlit Web Interface for CardioVex Sentinel AI.
Fully conversational, general-purpose RAG Chatbot.

To run:
    streamlit run app.py
"""

import streamlit as st
import time
from rag_engine import answer
from conversation import ConversationManager

st.set_page_config(
    page_title="CardioVex Sentinel AI — Clinical Protocol Chatbot",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for conversation memory
if "conversation" not in st.session_state:
    st.session_state.conversation = ConversationManager()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.title("🛡️ CardioVex Sentinel AI")
    st.caption("Phase III Protocol & Pharmacovigilance Assistant")
    st.markdown("---")
    
    st.markdown("### 📚 Knowledge Corpus")
    st.info("📄 `cardiovex_clinical_trial_protocol_50p.pdf`\n\n• **50 Pages**\n• **238 Semantic Chunks**\n• **Persistent ChromaDB**")
    
    st.markdown("### 💡 Sample Prompts")
    quick_queries = [
        "What is the minimum eGFR required for inclusion?",
        "Within how many hours must an SAE be reported?",
        "What is the storage temperature for reconstituted vials?",
        "What are the rules for prohibited CYP3A4 inhibitors?",
        "What are the informed consent audit requirements?",
        "What is the wholesale price in pharmacies? (Negative Test)",
        "What is amoxicillin dosage? (Negative Test)"
    ]
    for q in quick_queries:
        if st.button(q, key=f"btn_{q[:20]}"):
            st.session_state.selected_prompt = q

    st.markdown("---")
    if st.button("🗑️ Clear Chat History"):
        st.session_state.conversation.clear()
        st.session_state.messages = []
        st.rerun()

# Main Chat View
st.subheader("💬 CardioVex (CVX-409) Protocol Chatbot")
st.markdown("Ask **any question** about the Phase III trial protocol. Supports multi-turn follow-ups (*'Why?'*, *'What happens next?'*, *'What about SAEs?'*, *'Summarize it'*).")

# Display initial greeting if chat is empty
if not st.session_state.messages:
    with st.chat_message("assistant", avatar="🛡️"):
        st.markdown(
            "Hello! I am **CardioVex Sentinel AI**, your general-purpose conversational assistant for the **CardioVex (CVX-409) Phase III Protocol**.\n\n"
            "I retrieve information dynamically across all 50 pages of the protocol. If a topic is not documented in the protocol, I strictly return `[not found]`."
        )

# Render existing chat history
for msg in st.session_state.messages:
    role = msg["role"]
    avatar = "👤" if role == "user" else "🛡️"
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg["content"])
        if role == "assistant" and "sources" in msg and msg["sources"]:
            sources_str = ", ".join([f"`{s}`" for s in msg["sources"]])
            st.caption(f"📍 **Source Provenance:** {sources_str} | ⚡ Latency: {msg.get('latency', '0.0')}s")

# Check if a prompt was selected from sidebar buttons
prompt_to_send = st.session_state.pop("selected_prompt", None)
user_input = st.chat_input("Ask any question regarding the protocol...") or prompt_to_send

if user_input:
    # 1. Display user query
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    # 2. Generate response with conversation history
    with st.chat_message("assistant", avatar="🛡️"):
        with st.spinner("Searching ChromaDB vector store and synthesizing evidence..."):
            start_t = time.time()
            history_turns = st.session_state.conversation.get_history()
            res = answer(user_input, history=history_turns)
            elapsed = round(time.time() - start_t, 3)

            bot_ans = res.get("answer", "[not found]")
            sources = res.get("sources", [])

            # Update conversation memory
            st.session_state.conversation.add_message("user", user_input)
            st.session_state.conversation.add_message("assistant", bot_ans)

            st.markdown(bot_ans)
            if sources:
                sources_str = ", ".join([f"`{s}`" for s in sources])
                st.caption(f"📍 **Source Provenance:** {sources_str} | ⚡ Latency: {elapsed}s")
            elif bot_ans == "[not found]":
                st.caption("⚠️ **Notice:** Topic is not documented in the Phase III trial protocol.")

            # Record in session state
            st.session_state.messages.append({
                "role": "assistant",
                "content": bot_ans,
                "sources": sources,
                "latency": elapsed
            })
