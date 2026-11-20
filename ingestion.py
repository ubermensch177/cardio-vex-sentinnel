"""
Ingestion and Vector Store Management Module for CardioVex Sentinel AI.
Extracts all 50 pages of the protocol PDF (supporting PyMuPDF / PyPDF),
performs semantic text chunking (800–1200 characters with 200 overlap),
and persists dense embeddings into ChromaDB.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple
import chromadb
from chromadb.utils import embedding_functions

from config import (
    PDF_PATH,
    CHROMA_PERSIST_DIR,
    COLLECTION_NAME,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)

# Optional PyMuPDF (fitz) import with seamless fallback to pypdf
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

import pypdf


def load_pdf(pdf_path: Path | str = PDF_PATH) -> List[Dict]:
    """
    Extracts text from each page of the protocol PDF, capturing page numbers and section headers.
    Supports both PyMuPDF and PyPDF.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"Assigned PDF not found at path: {pdf_path}")

    pages_data = []

    if HAS_PYMUPDF:
        doc = fitz.open(str(pdf_path))
        for idx in range(len(doc)):
            page_num = idx + 1
            raw_text = doc[idx].get_text() or ""
            pages_data.append(_parse_page_text(page_num, raw_text))
        doc.close()
    else:
        reader = pypdf.PdfReader(str(pdf_path))
        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            raw_text = page.extract_text() or ""
            pages_data.append(_parse_page_text(page_num, raw_text))

    return pages_data


def _parse_page_text(page_num: int, raw_text: str) -> Dict:
    """Extracts Chapter, Module, and Section headers from raw page text."""
    module_match = re.search(r"(CHAPTER \d+ \| MODULE [^\n=]+)", raw_text)
    module_title = module_match.group(1).strip() if module_match else f"Module (Page {page_num})"

    sec_match = re.search(r"(SECTION \d+\.\d+:[^\n]+)", raw_text)
    section_title = sec_match.group(1).strip() if sec_match else "General Protocol Guidelines"

    return {
        "page_num": page_num,
        "module": module_title,
        "section": section_title,
        "text": raw_text.strip()
    }


def split_into_sentences(text: str) -> List[str]:
    """Splits text into clean sentence units without breaking abbreviations."""
    cleaned = re.sub(r"[ \t]+", " ", text)
    cleaned = re.sub(r"\n+", "\n", cleaned)
    sentence_end = re.compile(r"(?<=[.!?])\s+")
    raw_sentences = sentence_end.split(cleaned)
    return [s.strip() for s in raw_sentences if s.strip()]


def chunk_document(
    pages_data: List[Dict],
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[Dict]:
    """
    Chunks document pages using sentence boundaries (approx 800–1200 characters)
    with overlap, maintaining complete semantic coherence and rich page metadata.
    """
    all_chunks = []

    for page_info in pages_data:
        page_num = page_info["page_num"]
        page_text = page_info["text"]
        module = page_info["module"]
        section = page_info["section"]

        sentences = split_into_sentences(page_text)
        if not sentences:
            continue

        curr_chunk_sentences: List[str] = []
        curr_len = 0
        page_chunk_index = 1

        for sentence in sentences:
            sentence_len = len(sentence)
            if curr_len + sentence_len + 1 > chunk_size and curr_chunk_sentences:
                chunk_text = " ".join(curr_chunk_sentences).strip()
                chunk_id = f"p{page_num}_c{page_chunk_index}"
                all_chunks.append({
                    "id": chunk_id,
                    "text": chunk_text,
                    "metadata": {
                        "chunk_id": chunk_id,
                        "page": page_num,
                        "page_label": f"Page {page_num}",
                        "module": module,
                        "section": section,
                        "char_count": len(chunk_text)
                    }
                })
                page_chunk_index += 1

                # Retain overlap sentences
                overlap_sentences: List[str] = []
                overlap_len = 0
                for prev_s in reversed(curr_chunk_sentences):
                    if overlap_len + len(prev_s) <= chunk_overlap or not overlap_sentences:
                        overlap_sentences.insert(0, prev_s)
                        overlap_len += len(prev_s) + 1
                    else:
                        break

                curr_chunk_sentences = overlap_sentences + [sentence]
                curr_len = sum(len(s) + 1 for s in curr_chunk_sentences)
            else:
                curr_chunk_sentences.append(sentence)
                curr_len += sentence_len + 1

        if curr_chunk_sentences:
            chunk_text = " ".join(curr_chunk_sentences).strip()
            chunk_id = f"p{page_num}_c{page_chunk_index}"
            all_chunks.append({
                "id": chunk_id,
                "text": chunk_text,
                "metadata": {
                    "chunk_id": chunk_id,
                    "page": page_num,
                    "page_label": f"Page {page_num}",
                    "module": module,
                    "section": section,
                    "char_count": len(chunk_text)
                }
            })

    return all_chunks


def get_embedding_function():
    """Returns local ONNX-based dense vector embedding function."""
    return embedding_functions.DefaultEmbeddingFunction()


def build_vectorstore(force_rebuild: bool = False) -> Tuple[chromadb.PersistentClient, chromadb.Collection, bool]:
    """
    Initializes persistent ChromaDB vector store.
    If database is already persisted and populated with matching chunks, reloads without re-embedding.
    """
    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
    emb_fn = get_embedding_function()

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=emb_fn,
        metadata={"description": "CardioVex Phase III Protocol Embeddings (1000 chars)"}
    )

    current_count = collection.count()

    # If already populated and no force_rebuild
    if current_count > 0 and not force_rebuild:
        return client, collection, False

    # Rebuild collection
    if current_count > 0:
        client.delete_collection(name=COLLECTION_NAME)
        collection = client.create_collection(
            name=COLLECTION_NAME,
            embedding_function=emb_fn,
            metadata={"description": "CardioVex Phase III Protocol Embeddings (1000 chars)"}
        )

    pages = load_pdf(PDF_PATH)
    chunks = chunk_document(pages, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

    batch_size = 64
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        ids = [c["id"] for c in batch]
        documents = [c["text"] for c in batch]
        metadatas = [c["metadata"] for c in batch]
        collection.add(ids=ids, documents=documents, metadatas=metadatas)

    return client, collection, True


if __name__ == "__main__":
    print(f"Ingesting PDF: {PDF_PATH}")
    client, collection, reindexed = build_vectorstore(force_rebuild=True)
    print(f"Collection status: {collection.count()} chunks. Reindexed: {reindexed}")
