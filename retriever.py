"""
Retriever Module for CardioVex Sentinel AI.
Performs semantic retrieval against the persistent ChromaDB collection.
"""

from typing import Dict, List, Optional
import chromadb
from config import TOP_K, DISTANCE_THRESHOLD
from ingestion import build_vectorstore


class ProtocolRetriever:
    """Manages semantic search and context retrieval from ChromaDB."""

    def __init__(self, client: Optional[chromadb.PersistentClient] = None, collection: Optional[chromadb.Collection] = None):
        if client is None or collection is None:
            self.client, self.collection, _ = build_vectorstore()
        else:
            self.client = client
            self.collection = collection

    def retrieve(self, query: str, top_k: int = TOP_K) -> List[Dict]:
        """
        Retrieves the top-k most relevant chunks for a given query string.
        Returns a list of structured chunk records.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        retrieved_chunks = []
        if not results or not results["documents"] or not results["documents"][0]:
            return retrieved_chunks

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]
        ids = results["ids"][0]

        for doc_id, doc_text, meta, dist in zip(ids, documents, metadatas, distances):
            retrieved_chunks.append({
                "id": doc_id,
                "text": doc_text,
                "metadata": meta,
                "page": meta.get("page"),
                "page_label": meta.get("page_label", f"Page {meta.get('page')}"),
                "distance": float(dist),
                "section": meta.get("section", ""),
                "module": meta.get("module", "")
            })

        return retrieved_chunks

    def filter_by_threshold(
        self, chunks: List[Dict], threshold: float = DISTANCE_THRESHOLD
    ) -> List[Dict]:
        """Filters retrieved chunks by maximum allowable distance."""
        return [c for c in chunks if c["distance"] <= threshold]


if __name__ == "__main__":
    retriever = ProtocolRetriever()
    test_q = "What is the eGFR threshold for patient eligibility?"
    results = retriever.retrieve(test_q, top_k=2)
    for r in results:
        print(f"[{r['page_label']} | Dist: {r['distance']:.4f}] {r['text'][:120]}...")
