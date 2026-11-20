"""
Main Application and CLI Interface for CardioVex Sentinel AI.
Provides an interactive multi-turn conversational terminal chatbot, assessment runner,
and vector store index rebuilder.

Exports:
    def answer(question: str) -> dict
"""

import sys
import argparse
from typing import Dict
from rag_engine import answer
from run_assessment import run_assessment
from ingestion import build_vectorstore
from conversation import ConversationManager


def print_banner():
    banner = r"""
   _____              _ _    __      __            _____            _   _            _ 
  / ____|            | (_)   \ \    / /           / ____|          | | (_)          | |
 | |     __ _ _ __ __| |_  ___\ \  / /____  __   | (___   ___ _ __ | |_ _ _ __   ___| |
 | |    / _` | '__/ _` | |/ _ \\ \/ // _ \ \/ /    \___ \ / _ \ '_ \| __| | '_ \ / _ \ |
 | |___| (_| | | | (_| | | (_) |\  /|  __/>  <     ____) |  __/ | | | |_| | | | |  __/ |
  \_____\__,_|_|  \__,_|_|\___/  \/  \___/_/\_\   |_____/ \___|_| |_|\__|_|_| |_|\___|_|
                     Phase III Protocol & Pharmacovigilance Chatbot
    """
    print(banner)


def cli():
    parser = argparse.ArgumentParser(
        description="CardioVex Sentinel AI - Conversational Clinical Protocol RAG Chatbot"
    )
    parser.add_argument(
        "--question", "-q",
        type=str,
        help="Single question to query against the CardioVex clinical trial protocol."
    )
    parser.add_argument(
        "--assess", "-a",
        action="store_true",
        help="Run the complete 5-question protocol assessment suite."
    )
    parser.add_argument(
        "--rebuild-index",
        action="store_true",
        help="Force rebuild and re-embed the persistent ChromaDB collection."
    )

    args = parser.parse_args()

    if args.rebuild_index:
        print("[*] Rebuilding persistent ChromaDB vector store (1000 chars, 200 overlap)...")
        client, collection, reindexed = build_vectorstore(force_rebuild=True)
        print(f"[✓] Vector store rebuilt successfully with {collection.count()} chunks.")
        return

    if args.assess:
        print_banner()
        run_assessment()
        return

    if args.question:
        print(f"[*] Querying Protocol: {args.question}")
        res = answer(args.question)
        print(f"\n[Answer]: {res['answer']}")
        print(f"[Sources]: {res['sources']}")
        return

    # Interactive multi-turn conversational mode
    print_banner()
    print("Conversational Protocol Chatbot initialized with multi-turn memory.")
    print("You can ask any question, follow-up ('Why?', 'What if they fail?', 'What about SAEs?'),")
    print("type 'assess' to run benchmark, 'clear' to reset dialogue, or 'exit' to quit.\n")

    cm = ConversationManager()

    while True:
        try:
            user_input = input("\nClinician / You > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Session closed.")
                break
            if user_input.lower() in ["clear", "reset", "/clear"]:
                cm.clear()
                print("[✓] Conversation memory cleared.")
                continue
            if user_input.lower() in ["assess", "benchmark", "test"]:
                run_assessment()
                continue

            # Pass multi-turn history
            res = answer(user_input, history=cm.get_history())
            cm.add_message("user", user_input)
            cm.add_message("assistant", res["answer"])

            print("\n" + "—" * 65)
            print(f"Sentinel AI: {res['answer']}")
            sources_str = ", ".join(res["sources"]) if res["sources"] else "None (Ungrounded Topic)"
            print(f"Sources    : {sources_str}")
            print("—" * 65)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break


if __name__ == "__main__":
    cli()
