"""
Main Application and CLI Interface for CardioVex Sentinel AI.
Provides interactive querying, assessment suite execution, and vector store management.

Exports:
    def answer(question: str) -> dict
"""

import sys
import argparse
from typing import Dict
from rag_engine import answer
from run_assessment import run_assessment
from ingestion import build_vectorstore


def print_banner():
    banner = r"""
   _____              _ _    __      __            _____            _   _            _ 
  / ____|            | (_)   \ \    / /           / ____|          | | (_)          | |
 | |     __ _ _ __ __| |_  ___\ \  / /____  __   | (___   ___ _ __ | |_ _ _ __   ___| |
 | |    / _` | '__/ _` | |/ _ \\ \/ // _ \ \/ /    \___ \ / _ \ '_ \| __| | '_ \ / _ \ |
 | |___| (_| | | | (_| | | (_) |\  /|  __/>  <     ____) |  __/ | | | |_| | | | |  __/ |
  \_____\__,_|_|  \__,_|_|\___/  \/  \___/_/\_\   |_____/ \___|_| |_|\__|_|_| |_|\___|_|
                     Phase III Protocol & Pharmacovigilance Assistant
    """
    print(banner)


def cli():
    parser = argparse.ArgumentParser(
        description="CardioVex Sentinel AI - Clinical Trial Protocol RAG Assistant"
    )
    parser.add_argument(
        "--question", "-q",
        type=str,
        help="Question to query against the CardioVex clinical trial protocol."
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
        print("[*] Rebuilding persistent ChromaDB vector store...")
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

    # Interactive mode if no arguments provided
    print_banner()
    print("Interactive Protocol Assistant initialized.")
    print("Type your protocol question below, or 'assess' to run the benchmark, or 'exit' to quit.\n")

    while True:
        try:
            user_input = input("\nQuery [or 'assess'/'exit'] > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Session closed.")
                break
            if user_input.lower() in ["assess", "benchmark", "test"]:
                run_assessment()
                continue

            res = answer(user_input)
            print("\n---------------------------------------------------------")
            print(f"Answer : {res['answer']}")
            print(f"Sources: {res['sources']}")
            print("---------------------------------------------------------")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break


if __name__ == "__main__":
    cli()
