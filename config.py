"""
Configuration Module for CardioVex Sentinel AI.
Loads settings from .env file or system environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file if it exists
load_dotenv(BASE_DIR / ".env")

# Project Metadata
PROJECT_NAME = "CardioVex Sentinel AI"
PROJECT_SUBTITLE = "Phase III Clinical Trial Protocol & Pharmacovigilance Assistant"
CORPUS_FILENAME = os.getenv("PDF_PATH", "cardiovex_clinical_trial_protocol_50p.pdf")
PDF_PATH = BASE_DIR / CORPUS_FILENAME

# ChromaDB Settings
CHROMA_PERSIST_DIR = BASE_DIR / os.getenv("CHROMA_PERSIST_DIR", "chroma_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "cardiovex_phase3_protocol")

# Text Chunking Settings
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "600"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))

# Retrieval Settings
TOP_K = int(os.getenv("TOP_K", "4"))
DISTANCE_THRESHOLD = float(os.getenv("DISTANCE_THRESHOLD", "0.98"))

# Optional LLM API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
