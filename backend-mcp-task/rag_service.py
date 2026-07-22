import os
import tempfile
import traceback
from typing import List, Dict, Optional
from pdfminer.high_level import extract_text
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from config import Config
from tcs_embeddings import TCSGenAIEmbeddings

class RAGService:
    def __init__(self):
        print("[RAG] Loading TCS GenAI embedding model for Task Routing...")
        self.embedding_model = None
        self.embeddings_available = False
        
        try:
            if Config.GENAI_API_KEY and Config.GENAI_API_KEY not in ["YOUR_KEY_HERE", ""]:
                self.embedding_model = TCSGenAIEmbeddings()
                self.embeddings_available = True
                print("[RAG] [OK] TCS GenAI embedding model initialized successfully")
            else:
                print("[RAG] [WARN] GenAI API key not configured")
        except Exception as e:
            print(f"[RAG] [ERROR] Could not initialize TCS GenAI embeddings: {str(e)}")
            
        self.persist_directory = "./data/faiss_knowledge_docs"
        os.makedirs(self.persist_directory, exist_ok=True)
        self.vectordb_path = os.path.join(self.persist_directory, "vectordb.faiss")
        
        self.vectordb = None
        if self.embeddings_available:
            try:
                # FAISS saves locally under the directory
                if os.path.exists(os.path.join(self.persist_directory, "index.faiss")) or os.path.exists(os.path.join(self.persist_directory, "vectordb.faiss")):
                    self.vectordb = FAISS.load_local(
                        self.persist_directory,
                        self.embedding_model,
                        "vectordb",
                        allow_dangerous_deserialization=True
                    )
                    print("[RAG] [OK] Loaded existing FAISS vector store")
                else:
                    print("[RAG] No existing vector store found")
            except Exception as e:
                self.vectordb = None
                print(f"[RAG] Could not load vector store: {e}")

    def upload_document(self, file_content: bytes, filename: str, category: str = "General") -> Dict:
        """Upload and index PDF or TXT document using TCS GenAI embeddings"""
        if not self.embeddings_available:
            return {
                "success": False,
                "message": "Embedding model not available. Please check GenAI API key configuration.",
                "chunks_indexed": 0
            }
            
        try:
            raw_text = ""
            if filename.lower().endswith('.pdf'):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                    temp_file.write(file_content)
                    temp_file_path = temp_file.name
                print(f"[RAG] Extracting text from PDF {filename}...")
                raw_text = extract_text(temp_file_path)
                os.unlink(temp_file_path)
            else:
                print(f"[RAG] Reading text from TXT {filename}...")
                raw_text = file_content.decode('utf-8', errors='ignore')
                
            if not raw_text or len(raw_text.strip()) < 50:
                return {
                    "success": False,
                    "message": "Could not extract meaningful text from document",
                    "chunks_indexed": 0
                }
                
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            chunks = text_splitter.split_text(raw_text)
            print(f"[RAG] Split {filename} into {len(chunks)} chunks")
            
            metadatas = [{"source": filename, "category": category, "chunk": i} for i in range(len(chunks))]
            
            if self.vectordb is None:
                print("[RAG] Creating new FAISS vector store...")
                self.vectordb = FAISS.from_texts(
                    chunks,
                    self.embedding_model,
                    metadatas=metadatas
                )
            else:
                print("[RAG] Adding chunks to existing vector store...")
                self.vectordb.add_texts(chunks, metadatas=metadatas)
                
            self.vectordb.save_local(self.persist_directory, "vectordb")
            print("[RAG] Vector store saved successfully.")
            
            return {
                "success": True,
                "message": f"Successfully indexed {filename}",
                "chunks_indexed": len(chunks),
                "filename": filename
            }
        except Exception as e:
            traceback.print_exc()
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "chunks_indexed": 0
            }

    def search_knowledge(self, query: str, top_k: int = 5, category: Optional[str] = None) -> List[Dict]:
        """Search corporate knowledge base"""
        if self.vectordb is None:
            return []
            
        try:
            docs = self.vectordb.similarity_search(query, k=top_k * 2)
            
            results = []
            for doc in docs:
                if category and doc.metadata.get("category") != category:
                    continue
                results.append({
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "Unknown"),
                    "category": doc.metadata.get("category", "General")
                })
                if len(results) >= top_k:
                    break
            return results
        except Exception as e:
            print(f"[RAG] Search failed: {str(e)}")
            return []

    def add_document_to_rag(self, file_content: bytes, filename: str, metadata: Dict) -> Dict:
        """Add a document to RAG vector store with metadata"""
        if not self.embeddings_available:
            return {
                "success": False,
                "message": "Embeddings not available. Cannot add documents to RAG."
            }
            
        try:
            raw_text = ""
            if filename.lower().endswith('.pdf'):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                    temp_file.write(file_content)
                    temp_file_path = temp_file.name
                raw_text = extract_text(temp_file_path)
                os.unlink(temp_file_path)
            else:
                raw_text = file_content.decode('utf-8', errors='ignore')
                
            if not raw_text or len(raw_text.strip()) < 50:
                return {
                    "success": False,
                    "message": "Could not extract meaningful text from document"
                }
                
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            chunks = text_splitter.split_text(raw_text)
            
            docs_metadata = []
            for i in range(len(chunks)):
                meta = metadata.copy()
                meta.update({"chunk": i})
                docs_metadata.append(meta)
                
            if self.vectordb is None:
                self.vectordb = FAISS.from_texts(
                    chunks,
                    self.embedding_model,
                    metadatas=docs_metadata
                )
            else:
                self.vectordb.add_texts(chunks, metadatas=docs_metadata)
                
            self.vectordb.save_local(self.persist_directory, "vectordb")
            
            return {
                "success": True,
                "message": f"Successfully indexed {len(chunks)} chunks from {filename}",
                "chunks_added": len(chunks),
                "filename": filename
            }
        except Exception as e:
            traceback.print_exc()
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }

    def get_rag_statistics(self) -> Dict:
        """Get statistics about the RAG vector store"""
        if self.vectordb is None:
            return {
                "total_chunks": 0,
                "total_documents": 0,
                "documents": []
            }
        
        try:
            total_chunks = len(self.vectordb.docstore._dict)
            document_map = {}
            for doc_id, doc in self.vectordb.docstore._dict.items():
                filename = doc.metadata.get('filename', 'Unknown')
                if filename not in document_map:
                    document_map[filename] = {
                        "filename": filename,
                        "chunks": 0,
                        "upload_date": doc.metadata.get('upload_date', 'Unknown'),
                        "file_type": doc.metadata.get('file_type', 'Unknown'),
                        "category": doc.metadata.get('category', 'General')
                    }
                document_map[filename]["chunks"] += 1
            
            documents_list = list(document_map.values())
            
            return {
                "total_chunks": total_chunks,
                "total_documents": len(documents_list),
                "documents": documents_list
            }
        except Exception as e:
            print(f"[ERROR] Failed to get RAG statistics: {str(e)}")
            return {
                "total_chunks": 0,
                "total_documents": 0,
                "documents": [],
                "error": str(e)
            }

    def load_market_news(self) -> Dict:
        """Seed RAG database with default corporate policies"""
        policy_text = """
        CORPORATE ASSIGNMENT POLICY:
        - Any high complexity development task must be assigned to a resource with at least 5 years of experience.
        - Security-related code reviews require certified engineers and Daniel Martinez is the primary lead.
        - React development projects should prioritize developers with UX certifications.
        """
        metadata = {
            "filename": "default_corporate_policy.txt",
            "upload_date": "2026-07-16T12:00:00",
            "uploaded_by": "System",
            "file_type": "txt",
            "category": "Policy"
        }
        return self.add_document_to_rag(policy_text.encode('utf-8'), "default_corporate_policy.txt", metadata)
