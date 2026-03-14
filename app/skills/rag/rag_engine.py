import os
import shutil
from dotenv import load_dotenv

load_dotenv()

from typing import List
from langchain_community.document_loaders import (
    TextLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader
)
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.core.llm.embeddings import Qwen3VLEmbeddings
from app.core.llm.reranker import Qwen3VLReranker
from app.skills.ocr.ocr_engine import ocr_engine

from app.infrastructure.config import settings

VECTOR_STORE_PATH = os.path.join("data", "vector_store_faiss")


class RAGEngine:
    def __init__(self, persist_directory: str = VECTOR_STORE_PATH):
        self.persist_directory = persist_directory

        print("Initializing RAG Engine with Local Embedding models...")
        self.embeddings = Qwen3VLEmbeddings()

        self.reranker = Qwen3VLReranker()

        self._vectorstore = None
        if os.path.exists(self.persist_directory) and os.path.exists(os.path.join(self.persist_directory, "index.faiss")):
            try:
                print(f"Loading FAISS index from {self.persist_directory}")
                self._vectorstore = FAISS.load_local(
                    self.persist_directory,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
            except Exception as e:
                print(f"Failed to load FAISS index: {e}")
                self._vectorstore = None
        else:
            print("No existing FAISS index found. Initializing new one on first document addition.")
            self._vectorstore = None

    def add_knowledge_base(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"未找到文件: {file_path}")

        docs = []
        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext in [".pdf", ".png", ".jpg", ".jpeg", ".webp", ".tiff", ".bmp"]:
                print(f"Using Local OCR for {file_path}...")
                text = ocr_engine.process_file(file_path)
                if text:
                    docs = [Document(page_content=text, metadata={"source": file_path})]
                else:
                    print(f"Warning: OCR extracted no text from {file_path}")
            elif ext == ".docx":
                loader = Docx2txtLoader(file_path)
                docs = loader.load()
            elif ext == ".xlsx":
                loader = UnstructuredExcelLoader(file_path)
                docs = loader.load()
            elif ext == ".md":
                loader = TextLoader(file_path, encoding='utf-8')
                docs = loader.load()
            elif ext == ".txt":
                loader = TextLoader(file_path, encoding='utf-8')
                docs = loader.load()
            else:
                raise ValueError(f"不支持的文件类型: {ext}")
        except Exception as e:
            print(f"加载文件 {file_path} 错误: {e}")
            return False

        if not docs:
            return False

        print("正在使用语义切分 (Semantic Chunking)...")
        text_splitter = SemanticChunker(
            self.embeddings,
            breakpoint_threshold_type="percentile"
        )
        splits = text_splitter.split_documents(docs)

        try:
            if self._vectorstore is None:
                self._vectorstore = FAISS.from_documents(splits, self.embeddings)
            else:
                self._vectorstore.add_documents(documents=splits)

            self._vectorstore.save_local(self.persist_directory)
            print(f"成功添加了来自 {file_path} 的 {len(splits)} 个块")
            return True
        except Exception as e:
            print(f"添加到向量存储错误: {e}")
            return False

    def retrieve_context(self, query: str, k: int = 3, fetch_k: int = 20):
        try:
            if self._vectorstore is None:
                return []

            candidates = self._vectorstore.similarity_search(query, k=fetch_k)
            if not candidates:
                return []

            print(f"Reranking {len(candidates)} documents...")
            candidate_texts = [doc.page_content for doc in candidates]
            reranked_results = self.reranker.rerank(query, candidate_texts, top_k=k)

            final_docs = []
            for _, score, idx in reranked_results:
                doc = candidates[idx]
                doc.metadata['rerank_score'] = score
                final_docs.append(doc)

            return final_docs
        except Exception as e:
            print(f"检索上下文错误: {e}")
            return []

    def clear(self):
        try:
            if os.path.exists(self.persist_directory):
                shutil.rmtree(self.persist_directory)
            self._vectorstore = None
            print("Vector store cleared.")
        except Exception as e:
            print(f"Error clearing vector store: {e}")


rag_engine = RAGEngine()
