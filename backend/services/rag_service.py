import json
import logging
from pathlib import Path
from typing import Iterable

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self, corpus_path: str = "backend/legal_rules/legal_corpus.txt") -> None:
        self.corpus_path = Path(corpus_path)
        self.vector_store = None
        self._fallback_chunks: list[str] = []
        
        # Cache configuration
        self.cache_dir = Path("backend/legal_rules/.embeddings_cache")
        self.index_path = self.cache_dir / "faiss_index"
        self.metadata_path = self.cache_dir / "metadata.json"
        
        # Initialize cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self._initialize_index()

    def _get_corpus_hash(self) -> str:
        """Calculate hash of corpus file for change detection"""
        import hashlib
        corpus_text = self.corpus_path.read_text(encoding="utf-8")
        return hashlib.md5(corpus_text.encode()).hexdigest()

    def _load_cached_index(self) -> bool:
        """Try to load cached FAISS index if it exists and is valid"""
        try:
            if not self.index_path.exists() or not self.metadata_path.exists():
                logger.info("No cached embeddings found")
                return False
            
            # Check if corpus has changed
            current_hash = self._get_corpus_hash()
            with open(self.metadata_path, "r") as f:
                metadata = json.load(f)
            
            if metadata.get("corpus_hash") != current_hash:
                logger.info("Corpus has changed, will regenerate embeddings")
                return False
            
            # Load cached index
            embeddings = OpenAIEmbeddings()
            self.vector_store = FAISS.load_local(
                str(self.index_path),
                embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info("✓ Loaded cached embeddings successfully")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to load cached embeddings: {e}")
            return False

    def _save_index_to_cache(self) -> None:
        """Save FAISS index and metadata to disk"""
        try:
            if self.vector_store is None:
                return
            
            # Save FAISS index
            self.vector_store.save_local(str(self.index_path))
            
            # Save metadata
            metadata = {
                "corpus_hash": self._get_corpus_hash(),
                "version": "1.0",
            }
            with open(self.metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"✓ Saved embeddings to cache: {self.index_path}")
            
        except Exception as e:
            logger.error(f"Failed to save embeddings to cache: {e}")

    def _initialize_index(self) -> None:
        """Initialize index, loading from cache if available, otherwise creating new"""
        # Try to load from cache first
        if self._load_cached_index():
            # Load fallback chunks for fallback search
            corpus_text = self.corpus_path.read_text(encoding="utf-8")
            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=80)
            self._fallback_chunks = splitter.split_text(corpus_text)
            return
        
        # Generate new embeddings
        logger.info("Generating new embeddings...")
        corpus_text = self.corpus_path.read_text(encoding="utf-8")
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=80)
        chunks = splitter.split_text(corpus_text)
        self._fallback_chunks = chunks
        docs = [Document(page_content=chunk) for chunk in chunks]

        try:
            embeddings = OpenAIEmbeddings()
            self.vector_store = FAISS.from_documents(docs, embeddings)
            logger.info("✓ Generated embeddings successfully")
            
            # Save to cache for future use
            self._save_index_to_cache()
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            self.vector_store = None

    def retrieve_clauses(self, query: str, top_k: int = 3) -> list[str]:
        if self.vector_store is not None:
            docs = self.vector_store.similarity_search(query, k=top_k)
            return [doc.page_content for doc in docs]

        query_terms = set(query.lower().split())

        def score(text: str) -> int:
            terms = set(text.lower().split())
            return len(query_terms.intersection(terms))

        ranked = sorted(self._fallback_chunks, key=score, reverse=True)
        return list(ranked[:top_k])
