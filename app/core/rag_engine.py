import os
import shutil
from dotenv import load_dotenv

# Ensure env vars are loaded before initializing global instances
load_dotenv()

from typing import List, Optional, Tuple
from langchain_community.document_loaders import (
    TextLoader, 
    Docx2txtLoader, 
    UnstructuredExcelLoader
)
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# Custom local models
from app.core.embeddings import Qwen3VLEmbeddings
from app.core.reranker import Qwen3VLReranker
from app.core.ocr_engine import ocr_engine

VECTOR_STORE_PATH = os.path.join("data", "vector_store_faiss")

class RAGEngine:
    def __init__(self, persist_directory: str = VECTOR_STORE_PATH):
        self.persist_directory = persist_directory
        
        # Initialize Embeddings (Local Qwen3-VL)
        print("Initializing RAG Engine with Local Qwen3-VL models...")
        self.embeddings = Qwen3VLEmbeddings()
        
        # Initialize Reranker
        self.reranker = Qwen3VLReranker()
        
        # Initialize VectorStore (FAISS)
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
        """
        将文件（PDF, DOCX, XLSX, MD, TXT, Images）摄取到向量存储中。
        使用 DeepSeek-OCR 处理 PDF 和 图像。
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"未找到文件: {file_path}")

        # 1. 加载文档
        docs = []
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext in [".pdf", ".png", ".jpg", ".jpeg", ".webp", ".tiff", ".bmp"]:
                print(f"Using DeepSeek-OCR for {file_path}...")
                text = ocr_engine.process_file(file_path)
                if text:
                    docs = [Document(page_content=text, metadata={"source": file_path})]
                else:
                    print(f"Warning: OCR extracted no text from {file_path}")
            elif ext == ".docx":
                loader = Docx2txtLoader(file_path)
                docs = loader.load()
            elif ext == ".xlsx":
                # UnstructuredExcelLoader usually requires mode="elements" or similar for good chunks,
                # but default might be fine for simple tables.
                loader = UnstructuredExcelLoader(file_path)
                docs = loader.load()
            elif ext == ".md":
                # UnstructuredMarkdownLoader is good but might require deps. Fallback to Text if needed.
                # using TextLoader for MD is often safer if 'unstructured' lib is minimal.
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

        # 2. 分割文本 (Semantic Chunking)
        # "按道理应该由llm来进行切分...而不是机械化切分" -> SemanticChunker uses embeddings to split.
        print("正在使用语义切分 (Semantic Chunking)...")
        text_splitter = SemanticChunker(
            self.embeddings,
            breakpoint_threshold_type="percentile" # default
        )
        splits = text_splitter.split_documents(docs)

        # 3. 添加到 VectorStore
        try:
            if self._vectorstore is None:
                self._vectorstore = FAISS.from_documents(splits, self.embeddings)
            else:
                self._vectorstore.add_documents(documents=splits)
            
            # Save to disk
            self._vectorstore.save_local(self.persist_directory)
            print(f"成功添加了来自 {file_path} 的 {len(splits)} 个块")
            return True
        except Exception as e:
            print(f"添加到向量存储错误: {e}")
            return False

    def retrieve_context(self, query: str, k: int = 3, fetch_k: int = 20) -> List[Document]:
        """
        检索查询的前 k 个相关文档。
        Process:
        1. Retrieval: Fetch 'fetch_k' docs using similarity search.
        2. Reranking: Use Qwen3-VL-Reranker to select top 'k'.
        """
        try:
            if self._vectorstore is None:
                return []
                
            # 1. Initial Retrieval (Recall)
            candidates = self._vectorstore.similarity_search(query, k=fetch_k)
            if not candidates:
                return []
                
            # 2. Reranking
            print(f"Reranking {len(candidates)} documents...")
            candidate_texts = [doc.page_content for doc in candidates]
            reranked_results = self.reranker.rerank(query, candidate_texts, top_k=k)
            
            # Map back to Documents
            # reranked_results is list of (text, score, original_index)
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
        """
        清除向量存储（危险！）
        """
        try:
            if os.path.exists(self.persist_directory):
                shutil.rmtree(self.persist_directory)
            self._vectorstore = None
            print("Vector store cleared.")
        except Exception as e:
            print(f"Error clearing vector store: {e}")

# Singleton instance could be created here if needed
rag_engine = RAGEngine()
