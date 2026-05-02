"""
modules/rag_engine.py — RAG Engine Module

Indexes 7 ISO PDF standards into a ChromaDB vector store on first startup,
then retrieves relevant chunks for each checker type with full citation metadata.

Requirement: 10.1 – 10.6
"""

import hashlib
import logging
import os
from pathlib import Path
from typing import Any

import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

import config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Document metadata — maps filename → full standard info for citations
# ---------------------------------------------------------------------------
STANDARD_METADATA: dict[str, dict[str, str]] = {
    "ISO-128-1-2020.pdf": {
        "standard_name": "ISO 128-1",
        "full_name": "ISO 128-1:2020",
        "title": "Technical product documentation — General principles of presentation — Part 1: Basic conventions",
        "year": "2020",
    },
    "ISO-128-2-2020.pdf": {
        "standard_name": "ISO 128-2",
        "full_name": "ISO 128-2:2020",
        "title": "General principles of presentation — Part 2: Basic conventions for lines",
        "year": "2020",
    },
    "ISO-128-3-2020.pdf": {
        "standard_name": "ISO 128-3",
        "full_name": "ISO 128-3:2020",
        "title": "General principles of presentation — Part 3: Views, sections and cuts",
        "year": "2020",
    },
    "ISO-129-1-2018.pdf": {
        "standard_name": "ISO 129-1",
        "full_name": "ISO 129-1:2018",
        "title": "Indication of dimensions and tolerances — Part 1: General principles",
        "year": "2018",
    },
    "ISO-DIS-129-2.pdf": {
        "standard_name": "ISO/DIS 129-2",
        "full_name": "ISO/DIS 129-2",
        "title": "Indication of dimensions and tolerances — Part 2: Tolerancing of form and position",
        "year": "N/A",
    },
    "ISO-1101-2017.pdf": {
        "standard_name": "ISO 1101",
        "full_name": "ISO 1101:2017",
        "title": "Geometrical product specifications (GPS) — Geometrical tolerancing",
        "year": "2017",
    },
    "ISO-7200-2004.pdf": {
        "standard_name": "ISO 7200",
        "full_name": "ISO 7200:2004",
        "title": "Technical product documentation — Title blocks",
        "year": "2004",
    },
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class RAGEngine:
    """
    Singleton-like RAG engine that loads or creates the ChromaDB vector store
    and provides retrieval methods for each checker type.
    """

    def __init__(self) -> None:
        self._embeddings = OpenAIEmbeddings(
            model=config.EMBEDDING_MODEL,
            openai_api_key=config.OPENAI_API_KEY,
        )
        self._vectorstore: Chroma | None = None

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def initialize(self, documents_dir: str = config.DOCUMENTS_DIR) -> None:
        """
        Initialize the vector store. If the Chroma DB already exists on disk,
        load it; otherwise index all PDFs from `documents_dir` first.

        This method should be called once at application startup.
        """
        persist_path = Path(config.CHROMA_PERSIST_DIR)

        # Check if we already have a persisted index
        if persist_path.exists() and _chroma_has_data(persist_path):
            logger.info("Loading existing ChromaDB from: %s", persist_path)
            self._vectorstore = Chroma(
                collection_name=config.CHROMA_COLLECTION_NAME,
                embedding_function=self._embeddings,
                persist_directory=str(persist_path),
            )
            count = self._vectorstore._collection.count()
            logger.info("ChromaDB loaded: %d chunks indexed.", count)
        else:
            logger.info("Building ChromaDB index from PDFs in: %s", documents_dir)
            self._build_index(documents_dir)

    def _build_index(self, documents_dir: str) -> None:
        """Parse PDFs, split into chunks, and insert into ChromaDB."""
        docs_path = Path(documents_dir)
        if not docs_path.exists():
            raise FileNotFoundError(f"Documents directory not found: {docs_path}")

        all_documents: list[Document] = []
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.RAG_CHUNK_SIZE,
            chunk_overlap=config.RAG_CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " "],
        )

        for pdf_filename, meta in STANDARD_METADATA.items():
            pdf_path = docs_path / pdf_filename
            if not pdf_path.exists():
                logger.warning("PDF not found, skipping: %s", pdf_path)
                continue

            logger.info("Indexing: %s", pdf_filename)
            pages = _extract_pdf_text(pdf_path)

            for page_num, page_text in enumerate(pages, start=1):
                if not page_text.strip():
                    continue
                chunks = splitter.split_text(page_text)
                for chunk_idx, chunk in enumerate(chunks):
                    all_documents.append(Document(
                        page_content=chunk,
                        metadata={
                            "source_file": pdf_filename,
                            "standard_name": meta["standard_name"],
                            "full_name": meta["full_name"],
                            "title": meta["title"],
                            "year": meta["year"],
                            "page": page_num,
                            "chunk": chunk_idx,
                        },
                    ))

        if not all_documents:
            logger.error("No documents were successfully loaded for indexing.")
            return

        logger.info("Indexing %d chunks into ChromaDB...", len(all_documents))
        self._vectorstore = Chroma.from_documents(
            documents=all_documents,
            embedding=self._embeddings,
            collection_name=config.CHROMA_COLLECTION_NAME,
            persist_directory=str(config.CHROMA_PERSIST_DIR),
        )
        logger.info("ChromaDB index built with %d chunks.", len(all_documents))

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def retrieve(
        self,
        query: str,
        checker_type: str | None = None,
        top_k: int = config.RAG_TOP_K,
    ) -> list[dict[str, Any]]:
        """
        Retrieve relevant standard chunks for a given query.

        Args:
            query: The question or content to search for.
            checker_type: One of "dimension", "annotation", "standard", or None.
                          Used to apply source-file filtering (priority documents).
            top_k: Number of chunks to return.

        Returns:
            List of dicts with keys: content, citation, source_file, page, score.
        """
        if self._vectorstore is None:
            logger.error("RAGEngine not initialized. Call initialize() first.")
            return []

        # Build source filter if checker_type specified
        where_filter = None
        if checker_type and checker_type in config.RAG_CHECKER_PRIORITY:
            priority_files = config.RAG_CHECKER_PRIORITY[checker_type]
            where_filter = {"source_file": {"$in": priority_files}}

        try:
            results = self._vectorstore.similarity_search_with_score(
                query=query,
                k=top_k,
                filter=where_filter,
            )
        except Exception as exc:
            logger.warning("Filtered retrieval failed (%s), retrying without filter: %s", checker_type, exc)
            # Fallback: retrieve without filter
            results = self._vectorstore.similarity_search_with_score(query=query, k=top_k)

        retrieved = []
        for doc, score in results:
            meta = doc.metadata
            citation = _format_citation(meta)
            retrieved.append({
                "content": doc.page_content,
                "citation": citation,
                "source_file": meta.get("source_file", ""),
                "standard_name": meta.get("standard_name", ""),
                "page": meta.get("page", 0),
                "score": float(score),
            })

        logger.debug("RAG retrieved %d chunks for query: %.80s...", len(retrieved), query)
        return retrieved

    def format_context(self, retrieved_chunks: list[dict[str, Any]]) -> str:
        """
        Format retrieved chunks into a single context string suitable for
        injection into a system prompt.

        Each chunk is formatted as:
            [Citation]
            Content...
        """
        if not retrieved_chunks:
            return "Không tìm thấy thông tin tiêu chuẩn liên quan trong cơ sở dữ liệu."

        parts = []
        for chunk in retrieved_chunks:
            parts.append(
                f"**{chunk['citation']}**\n{chunk['content']}"
            )
        return "\n\n---\n\n".join(parts)

    def is_initialized(self) -> bool:
        """Return True if the vector store has been loaded."""
        return self._vectorstore is not None


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_rag_engine: RAGEngine | None = None


def get_rag_engine() -> RAGEngine:
    """Return the global RAGEngine singleton, initializing it if necessary."""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
        _rag_engine.initialize()
    return _rag_engine


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _extract_pdf_text(pdf_path: Path) -> list[str]:
    """Extract text from each page of a PDF using pdfplumber."""
    pages = []
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                pages.append(text)
    except Exception as exc:
        logger.error("Failed to extract text from %s: %s", pdf_path, exc)
    return pages


def _format_citation(meta: dict[str, str]) -> str:
    """
    Format a standard citation string from chunk metadata.
    Format: [Standard Name] [Full Number] - Trang [N]: [Title]
    """
    full_name = meta.get("full_name", meta.get("standard_name", "ISO"))
    page = meta.get("page", "?")
    title = meta.get("title", "")
    return f"[{full_name}] - Trang {page}: {title}"


def _chroma_has_data(persist_path: Path) -> bool:
    """Check if ChromaDB directory contains indexed data."""
    # ChromaDB stores SQLite DB in the persist directory
    sqlite_file = persist_path / "chroma.sqlite3"
    return sqlite_file.exists() and sqlite_file.stat().st_size > 1024
