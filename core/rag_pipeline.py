"""RAG Pipeline for document retrieval and question answering.

This module provides a complete RAG (Retrieval-Augmented Generation) pipeline
built on top of LangChain with Milvus vector store and HuggingFace embeddings.

Integration Points:
- LangChain: DoclingLoader for document loading
- HuggingFace: Sentence transformers for embeddings
- Milvus: Vector database for similarity search
- Gradient SDK: Can be combined for AI-enhanced responses

Usage:
    >>> from core.rag_pipeline import DocumentRAGPipeline
    >>> pipeline = DocumentRAGPipeline()
    >>> pipeline.add_documents([Path("doc.pdf")])
    >>> answer = pipeline.query("What is the main topic?")
"""

from typing import List, Optional, Any
from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_milvus import Milvus
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from .langchain_loader import load_documents_for_rag, lazy_load_documents_for_rag


class DocumentRAGPipeline:
    """RAG pipeline for PDF document retrieval and querying.

    Provides document indexing, similarity search, and retriever interface
    for integration with LangChain chains and agents.

    Attributes:
        model_name: HuggingFace embedding model name
        embeddings: Initialized HuggingFaceEmbeddings instance
        vector_store: Milvus vector store (initialized on first add_documents call)
    """

    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        use_gpu: bool = True,
        collection_name: str = "docling_docs",
        db_path: str = "./docling.db"
    ):
        """Initialize the RAG pipeline.

        Args:
            embedding_model: HuggingFace model for embeddings
            use_gpu: Use CUDA for embeddings if available
            collection_name: Milvus collection name
            db_path: Path to Milvus lite database file
        """
        self.model_name = embedding_model
        self.collection_name = collection_name
        self.db_path = db_path

        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.model_name,
            model_kwargs={'device': 'cuda' if use_gpu else 'cpu'}
        )

        self.vector_store: Optional[Milvus] = None
        self._document_count: int = 0

    def add_documents(self, pdf_paths: List[Path]) -> int:
        """
        Load and index documents from PDF paths.

        Args:
            pdf_paths: List of paths to PDF files

        Returns:
            Number of document chunks indexed
        """
        docs = load_documents_for_rag(pdf_paths)

        if not docs:
            return 0

        if self.vector_store is None:
            # Initialize vector store with first batch of documents
            self.vector_store = Milvus.from_documents(
                documents=docs,
                embedding=self.embeddings,
                collection_name=self.collection_name,
                connection_args={"uri": self.db_path},
                drop_old=False
            )
        else:
            # Add to existing vector store
            self.vector_store.add_documents(docs)

        self._document_count += len(docs)
        return len(docs)

    def add_documents_lazy(self, pdf_paths: List[Path], batch_size: int = 100) -> int:
        """
        Load and index documents lazily for memory efficiency.

        Args:
            pdf_paths: List of paths to PDF files
            batch_size: Number of documents to process at a time

        Returns:
            Number of document chunks indexed
        """
        total_added = 0
        batch = []

        for doc in lazy_load_documents_for_rag(pdf_paths):
            batch.append(doc)

            if len(batch) >= batch_size:
                if self.vector_store is None:
                    self.vector_store = Milvus.from_documents(
                        documents=batch,
                        embedding=self.embeddings,
                        collection_name=self.collection_name,
                        connection_args={"uri": self.db_path},
                        drop_old=False
                    )
                else:
                    self.vector_store.add_documents(batch)

                total_added += len(batch)
                self._document_count += len(batch)
                batch = []

        # Process remaining documents
        if batch:
            if self.vector_store is None:
                self.vector_store = Milvus.from_documents(
                    documents=batch,
                    embedding=self.embeddings,
                    collection_name=self.collection_name,
                    connection_args={"uri": self.db_path},
                    drop_old=False
                )
            else:
                self.vector_store.add_documents(batch)

            total_added += len(batch)
            self._document_count += len(batch)

        return total_added

    @property
    def document_count(self) -> int:
        """Return the number of indexed document chunks."""
        return self._document_count

    def get_retriever(self, k: int = 4, **search_kwargs) -> VectorStoreRetriever:
        """Get a LangChain retriever for chain composition.

        Args:
            k: Number of documents to retrieve
            **search_kwargs: Additional search parameters

        Returns:
            VectorStoreRetriever for use in LangChain chains

        Raises:
            ValueError: If no documents have been indexed

        Example:
            >>> retriever = pipeline.get_retriever(k=5)
            >>> chain = RetrievalQA.from_chain_type(
            ...     llm=llm,
            ...     retriever=retriever
            ... )
        """
        if self.vector_store is None:
            raise ValueError("No documents indexed. Call add_documents first.")

        search_kwargs = {"k": k, **search_kwargs}
        return self.vector_store.as_retriever(search_kwargs=search_kwargs)

    def query(self, question: str, k: int = 4) -> str:
        """
        Query the RAG pipeline with similarity search.

        Args:
            question: Query string
            k: Number of documents to retrieve

        Returns:
            Concatenated context from retrieved documents
        """
        if self.vector_store is None:
            return "No documents indexed."

        # Retrieve relevant documents
        results = self.vector_store.similarity_search(question, k=k)

        # Format the retrieved docs into a single string
        return "\n\n---\n\n".join(doc.page_content for doc in results)

    def query_with_scores(self, question: str, k: int = 4) -> List[tuple]:
        """
        Query with relevance scores for result ranking.

        Args:
            question: Query string
            k: Number of documents to retrieve

        Returns:
            List of (Document, score) tuples sorted by relevance
        """
        if self.vector_store is None:
            return []

        return self.vector_store.similarity_search_with_score(question, k=k)
