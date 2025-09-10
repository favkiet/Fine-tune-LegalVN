"""
Legal QA Chatbot - Streamlit Application

A web-based chatbot for Vietnamese legal Q&A using RAG (Retrieval Augmented Generation)
with Qdrant vector database and Ollama LLM.
"""

import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from fastembed import SparseTextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
from qdrant_client import QdrantClient
from qdrant_client.models import models
import uuid
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import logging
import hashlib
import pickle
import os
from functools import lru_cache
import concurrent.futures

# LangChain imports
from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.schema import Document

dense_model_name = "sentence-transformers/all-MiniLM-L6-v2"
sparse_model_name = "Qdrant/bm25"
rerank_model_name = "jinaai/jina-reranker-v2-base-multilingual"
llm_model_name = "gemma3:1b"

# Cache directory
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('legal_qa_full.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Legal QA Chatbot",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left-color: #2196f3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left-color: #9c27b0;
    }
    .source-doc {
        background-color: #fff3e0;
        border-left-color: #ff9800;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

class LegalQASystem:
    """Main class for the Legal QA system with performance optimizations."""
    
    def __init__(self):
        self.collection_name = "thue-phi-le-phi_all-MiniLM-L6-v2"
        self.client = None
        self.dense_model = None
        self.sparse_model = None
        self.rerank_model = None
        self.llm = None
        self.initialized = False
        
        # Performance optimizations
        self.cache_enabled = True
        self.fast_mode = False
        self.query_cache = {}
        self.embedding_cache = {}
    
    def initialize(self):
        """Initialize all models and connections."""
        try:
            with st.spinner("🔄 Đang khởi tạo hệ thống..."):
                # Initialize Qdrant client with optimized settings
                try:
                    self.client = QdrantClient(
                        host="localhost",
                        port=6333,
                        timeout=30.0,  # Reduced timeout
                        prefer_grpc=False  # Use HTTP for compatibility
                    )
                    # Test connection
                    collections = self.client.get_collections()
                    logger.info("Qdrant client initialized successfully")
                    logger.info(f"Available collections: {[c.name for c in collections.collections]}")
                except Exception as e:
                    logger.error(f"Failed to connect to Qdrant: {e}")
                    # Try alternative connection methods
                    try:
                        self.client = QdrantClient(
                            host="127.0.0.1",
                            port=6333,
                            timeout=10.0,
                            prefer_grpc=False
                        )
                        collections = self.client.get_collections()
                        logger.info("Qdrant client connected with alternative settings")
                        logger.info(f"Available collections: {[c.name for c in collections.collections]}")
                    except Exception as e2:
                        logger.error(f"Alternative connection also failed: {e2}")
                        raise Exception(f"Cannot connect to Qdrant server. Please ensure Qdrant is running on localhost:6333. Error: {e}")
                
                # Initialize embedding models with caching
                self.dense_model = SentenceTransformer(dense_model_name)
                # Enable caching for sentence transformer
                self.dense_model.encode = lru_cache(maxsize=1000)(self.dense_model.encode)
                logger.info("Dense embedding model (SentenceTransformer) initialized with caching")
                
                self.sparse_model = SparseTextEmbedding(sparse_model_name)
                logger.info("Sparse embedding model (FastEmbed) initialized")
                
                self.rerank_model = TextCrossEncoder(rerank_model_name)
                logger.info("Rerank model (TextCrossEncoder) initialized")
                
                # Initialize LLM with optimized settings
                self.llm = ChatOllama(
                    model=llm_model_name,
                    temperature=0.1,
                    top_p=0.9,
                    num_ctx=2048,  # Reduced context window
                    num_predict=512,  # Limit response length
                    num_thread=4  # Optimize threading
                )
                logger.info("LLM (llama3.1:8b) initialized successfully")
                
                self.initialized = True
                logger.info("Full system initialization completed successfully")
                st.success("✅ Hệ thống đã sẵn sàng!")
                
        except Exception as e:
            logger.error(f"Failed to initialize full system: {str(e)}", exc_info=True)
            st.error(f"❌ Lỗi khởi tạo hệ thống: {str(e)}")
            self.initialized = False
    
    def _get_cache_key(self, query: str, top_k: int, rerank_top_k: int) -> str:
        """Generate cache key for query."""
        return hashlib.md5(f"{query}_{top_k}_{rerank_top_k}_{self.fast_mode}".encode()).hexdigest()
    
    def _load_from_cache(self, cache_key: str) -> Optional[List[Dict]]:
        """Load results from cache."""
        if not self.cache_enabled:
            return None
        
        cache_file = os.path.join(CACHE_DIR, f"{cache_key}.pkl")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                    logger.info(f"Cache hit for query: {cache_key[:10]}...")
                    return cached_data
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
        return None
    
    def _save_to_cache(self, cache_key: str, data: List[Dict]):
        """Save results to cache."""
        if not self.cache_enabled:
            return
        
        try:
            cache_file = os.path.join(CACHE_DIR, f"{cache_key}.pkl")
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
            logger.info(f"Saved to cache: {cache_key[:10]}...")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def retrieve_and_rerank_fast(self, query: str, top_k: int = 10, rerank_top_k: int = 5) -> List[Dict]:
        """Fast retrieval without reranking for speed."""
        logger.info(f"Fast retrieval for query: {query[:50]}...")
        
        if not self.initialized:
            return []
        
        # Check cache first
        cache_key = self._get_cache_key(query, top_k, rerank_top_k)
        cached_result = self._load_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Generate embeddings in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                dense_future = executor.submit(self.dense_model.encode, query)
                sparse_future = executor.submit(lambda: list(self.sparse_model.embed(query))[0])
                
                dense_vector_query = dense_future.result()
                bm25_query_vector = sparse_future.result()
            
            # Perform hybrid search with reduced parameters
            search_result = self.client.query_points(
                collection_name=self.collection_name,
                query=models.FusionQuery(
                    fusion=models.Fusion.RRF
                ),
                prefetch=[
                    models.Prefetch(
                        query=dense_vector_query,
                        using="dense",
                        limit=top_k
                    ),
                    models.Prefetch(
                        query=bm25_query_vector.as_object(),
                        using="bm25",
                        limit=top_k
                    ),
                ],
                with_payload=True,
                with_vectors=False,  # Don't need vectors for faster response
                limit=rerank_top_k  # Return fewer results
            ).points
            
            logger.info(f"Fast retrieval returned {len(search_result)} documents")
            
            # Prepare results without reranking
            results = []
            for rank, hit in enumerate(search_result, 1):
                results.append({
                    "rank": rank,
                    "id": hit.id,
                    "document": hit.payload["raw_context"],
                    "rerank_score": hit.score if hasattr(hit, 'score') else 1.0,
                    "original_score": hit.score if hasattr(hit, 'score') else None,
                    "create_at": hit.payload.get("create_at", "N/A")
                })
            
            # Cache the results
            self._save_to_cache(cache_key, results)
            return results
            
        except Exception as e:
            logger.error(f"Error in fast retrieval: {str(e)}", exc_info=True)
            return []
    
    def retrieve_and_rerank(self, query: str, top_k: int = 20, rerank_top_k: int = 10) -> List[Dict]:
        """Perform hybrid retrieval and reranking with caching."""
        logger.info(f"Starting retrieval and reranking for query: {query[:100]}...")
        logger.info(f"Parameters: top_k={top_k}, rerank_top_k={rerank_top_k}")
        
        if not self.initialized:
            return []
        
        # Check cache first
        cache_key = self._get_cache_key(query, top_k, rerank_top_k)
        cached_result = self._load_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Generate embeddings in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                dense_future = executor.submit(self.dense_model.encode, query)
                sparse_future = executor.submit(lambda: list(self.sparse_model.embed(query))[0])
                
                dense_vector_query = dense_future.result()
                bm25_query_vector = sparse_future.result()
            
            # Perform hybrid search
            logger.info(f"Performing hybrid search on collection: {self.collection_name}")
            search_result = self.client.query_points(
                collection_name=self.collection_name,
                query=models.FusionQuery(
                    fusion=models.Fusion.RRF
                ),
                prefetch=[
                    models.Prefetch(
                        query=dense_vector_query,
                        using="dense",
                        limit=top_k
                    ),
                    models.Prefetch(
                        query=bm25_query_vector.as_object(),
                        using="bm25",
                        limit=top_k
                    ),
                ],
                with_payload=True,
                with_vectors=False,  # Don't need vectors for faster response
                limit=top_k
            ).points
            
            logger.info(f"Retrieved {len(search_result)} documents from vector search")
            
            # Extract document texts for reranking (fewer documents)
            initial_hits = [hit.payload["raw_context"] for hit in search_result[:rerank_top_k]]
            
            if not initial_hits or not self.rerank_model:
                # Return without reranking if no rerank model or no hits
                results = []
                for rank, hit in enumerate(search_result[:rerank_top_k], 1):
                    results.append({
                        "rank": rank,
                        "id": hit.id,
                        "document": hit.payload["raw_context"],
                        "rerank_score": hit.score if hasattr(hit, 'score') else 1.0,
                        "original_score": hit.score if hasattr(hit, 'score') else None,
                        "create_at": hit.payload.get("create_at", "N/A")
                    })
                # Cache the results
                self._save_to_cache(cache_key, results)
                return results
            
            logger.info(f"Performing reranking on {len(initial_hits)} documents...")
            # Perform reranking
            new_scores = list(self.rerank_model.rerank(query, initial_hits))
            
            # Create ranking with original indices
            ranking = list(enumerate(new_scores))
            ranking.sort(key=lambda x: x[1], reverse=True)
            
            # Prepare results
            results = []
            for rank, (original_idx, rerank_score) in enumerate(ranking, 1):
                original_hit = search_result[original_idx]
                results.append({
                    "rank": rank,
                    "id": original_hit.id,
                    "document": original_hit.payload["raw_context"],
                    "rerank_score": rerank_score,
                    "original_score": original_hit.score if hasattr(original_hit, 'score') else None,
                    "create_at": original_hit.payload.get("create_at", "N/A")
                })
            
            # Cache the results
            self._save_to_cache(cache_key, results)
            logger.info(f"Reranking completed, returning {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error in retrieve_and_rerank: {str(e)}", exc_info=True)
            return []
    
    def generate_answer_fast(self, query: str, context_docs: List[str]) -> str:
        """Generate answer with optimized prompt and settings."""
        logger.info(f"Fast answer generation for query: {query[:50]}...")
        
        if not self.initialized or not context_docs:
            return "Xin lỗi, tôi không thể tạo câu trả lời vào lúc này."
        
        try:
            # Use only top 2 documents for faster processing
            context = "\n\n".join(context_docs[:2])
            logger.info(f"Context length: {len(context)} characters")
            
            # Optimized prompt template (shorter and more focused)
            prompt_template = PromptTemplate(
                input_variables=["context", "question"],
                template="""Dựa trên thông tin pháp lý sau, trả lời câu hỏi một cách ngắn gọn và chính xác:

Thông tin: {context}

Câu hỏi: {question}

Trả lời ngắn gọn:"""
            )
            
            # Create chain
            chain = prompt_template | self.llm | StrOutputParser()
            
            # Generate answer
            answer = chain.invoke({"context": context, "question": query})
            logger.info(f"Fast answer generated, length: {len(answer)} characters")
            return answer
            
        except Exception as e:
            logger.error(f"Error in fast answer generation: {str(e)}", exc_info=True)
            return "Xin lỗi, có lỗi xảy ra khi tạo câu trả lời."
    
    def generate_answer(self, query: str, context_docs: List[str]) -> str:
        """Generate answer using LLM with retrieved context."""
        logger.info(f"Generating answer for query: {query[:100]}...")
        logger.info(f"Number of context documents: {len(context_docs)}")
        
        if not self.initialized or not context_docs:
            return "Xin lỗi, tôi không thể tạo câu trả lời vào lúc này."
        
        try:
            # Create context from retrieved documents
            context = "\n\n".join(context_docs[:3])  # Use top 3 documents
            logger.info(f"Context length: {len(context)} characters")
            
            # Optimized prompt template
            prompt_template = PromptTemplate(
                input_variables=["context", "question"],
                template="""Bạn là chuyên gia tư vấn pháp luật Việt Nam. Trả lời dựa trên thông tin được cung cấp:

Thông tin pháp lý:
{context}

Câu hỏi: {question}

Trả lời:"""
            )
            
            # Create chain
            chain = prompt_template | self.llm | StrOutputParser()
            
            # Generate answer
            answer = chain.invoke({"context": context, "question": query})
            logger.info(f"Generated answer length: {len(answer)} characters")
            logger.info("Answer generation completed successfully")
            return answer
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}", exc_info=True)
            return "Xin lỗi, có lỗi xảy ra khi tạo câu trả lời."

def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "qa_system" not in st.session_state:
        st.session_state.qa_system = LegalQASystem()
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "performance_mode" not in st.session_state:
        st.session_state.performance_mode = "fast"  # fast, balanced, accurate

def display_chat_message(role: str, content: str, sources: List[Dict] = None, performance_info: str = None):
    """Display a chat message with performance info."""
    if role == "user":
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>👤 Bạn:</strong><br>
            {content}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message assistant-message">
            <strong>⚖️ Luật sư AI:</strong><br>
            {content}
        </div>
        """, unsafe_allow_html=True)
        
        # Display performance info
        if performance_info:
            st.markdown(f"""
            <div style="background-color: #e8f5e8; padding: 0.5rem; border-radius: 0.3rem; font-size: 0.8rem; color: #2e7d32; margin-top: 0.5rem;">
                {performance_info}
            </div>
            """, unsafe_allow_html=True)
        
        # Display sources if available
        if sources:
            with st.expander("📚 Nguồn tham khảo", expanded=False):
                for i, source in enumerate(sources[:3], 1):
                    st.markdown(f"""
                    <div class="source-doc">
                        <strong>Nguồn {i}:</strong><br>
                        {source['document'][:200]}...
                        <br><small>Điểm số: {source['rerank_score']:.3f}</small>
                    </div>
                    """, unsafe_allow_html=True)

def main():
    """Main application function."""
    
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">⚖️ Legal QA Chatbot</h1>', unsafe_allow_html=True)
    st.markdown("### Hệ thống tư vấn pháp luật Việt Nam sử dụng AI")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Cài đặt")
        
        # Performance mode selection
        st.subheader("🚀 Chế độ hiệu suất")
        performance_mode = st.selectbox(
            "Chọn chế độ:",
            ["fast", "balanced", "accurate"],
            index=0,
            format_func=lambda x: {
                "fast": "⚡ Nhanh (không rerank)",
                "balanced": "⚖️ Cân bằng",
                "accurate": "🎯 Chính xác (rerank đầy đủ)"
            }[x]
        )
        st.session_state.performance_mode = performance_mode
        
        # Initialize system button
        if st.button("🚀 Khởi tạo hệ thống", type="primary"):
            st.session_state.qa_system.initialize()
        
        # System status
        if st.session_state.qa_system.initialized:
            st.success("✅ Hệ thống đã sẵn sàng")
        else:
            st.warning("⚠️ Hệ thống chưa được khởi tạo")
            
        # Qdrant connection info
        st.info("""
        **🔧 Thông tin Qdrant:**
        - Container: sleepy_noyce
        - Port: 6333
        - Status: Đang chạy
        """)
        
        st.divider()
        
        # Settings based on performance mode
        st.subheader("🔧 Tham số tìm kiếm")
        
        if performance_mode == "fast":
            top_k = st.slider("Số lượng tài liệu tìm kiếm", 5, 20, 10)
            rerank_top_k = st.slider("Số lượng tài liệu hiển thị", 3, 10, 5)
        elif performance_mode == "balanced":
            top_k = st.slider("Số lượng tài liệu tìm kiếm", 10, 30, 15)
            rerank_top_k = st.slider("Số lượng tài liệu rerank", 5, 15, 8)
        else:  # accurate
            top_k = st.slider("Số lượng tài liệu tìm kiếm", 15, 50, 20)
            rerank_top_k = st.slider("Số lượng tài liệu rerank", 8, 20, 10)
        
        # Cache settings
        st.subheader("💾 Cache")
        cache_enabled = st.checkbox("Bật cache", value=True)
        st.session_state.qa_system.cache_enabled = cache_enabled
        
        if st.button("🗑️ Xóa cache"):
            import shutil
            if os.path.exists(CACHE_DIR):
                shutil.rmtree(CACHE_DIR)
                os.makedirs(CACHE_DIR, exist_ok=True)
            st.success("Cache đã được xóa!")
        
        st.divider()
        
        # Chat history
        st.subheader("💬 Lịch sử chat")
        if st.button("🗑️ Xóa lịch sử"):
            st.session_state.messages = []
            st.session_state.chat_history = []
            st.rerun()
    
    # Main chat interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Chat container
        chat_container = st.container()
        
        # Display chat history
        with chat_container:
            for message in st.session_state.messages:
                display_chat_message(
                    message["role"], 
                    message["content"], 
                    message.get("sources"),
                    message.get("performance_info")
                )
        
        # Chat input
        if prompt := st.chat_input("Nhập câu hỏi pháp luật của bạn..."):
            logger.info(f"User entered prompt: {prompt[:100]}...")
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            display_chat_message("user", prompt)
            
            # Generate response based on performance mode
            if st.session_state.qa_system.initialized:
                start_time = datetime.now()
                
                if performance_mode == "fast":
                    with st.spinner("⚡ Đang tìm kiếm nhanh..."):
                        retrieved_docs = st.session_state.qa_system.retrieve_and_rerank_fast(
                            prompt, top_k=top_k, rerank_top_k=rerank_top_k
                        )
                    
                    with st.spinner("🤖 Đang tạo câu trả lời nhanh..."):
                        context_docs = [doc["document"] for doc in retrieved_docs]
                        answer = st.session_state.qa_system.generate_answer_fast(prompt, context_docs)
                
                else:  # balanced or accurate
                    with st.spinner("🔍 Đang tìm kiếm thông tin..."):
                        retrieved_docs = st.session_state.qa_system.retrieve_and_rerank(
                            prompt, top_k=top_k, rerank_top_k=rerank_top_k
                        )
                    
                    with st.spinner("🤖 Đang tạo câu trả lời..."):
                        context_docs = [doc["document"] for doc in retrieved_docs]
                        answer = st.session_state.qa_system.generate_answer(prompt, context_docs)
                
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                performance_info = f"⚡ Thời gian phản hồi: {response_time:.2f}s | 📄 Tài liệu: {len(retrieved_docs)} | 🎯 Chế độ: {performance_mode}"
                
                # Add assistant message to chat history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": answer,
                    "sources": retrieved_docs,
                    "performance_info": performance_info
                })
                
                display_chat_message("assistant", answer, retrieved_docs, performance_info)
            else:
                logger.warning("System not initialized, showing error message")
                error_msg = "⚠️ Vui lòng khởi tạo hệ thống trước khi sử dụng."
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                display_chat_message("assistant", error_msg)
    
    with col2:
        # Statistics and info
        st.subheader("📊 Thống kê")
        
        if st.session_state.qa_system.initialized:
            # Get collection info
            try:
                collection_info = st.session_state.qa_system.client.get_collection(
                    st.session_state.qa_system.collection_name
                )
                
                st.metric("📄 Tổng tài liệu", f"{collection_info.points_count:,}")
                st.metric("💬 Số tin nhắn", len(st.session_state.messages))
                
                # Cache statistics
                cache_files = len([f for f in os.listdir(CACHE_DIR) if f.endswith('.pkl')])
                st.metric("💾 Cache entries", cache_files)
                
            except Exception as e:
                st.error(f"Lỗi lấy thông tin: {str(e)}")
        
        st.divider()
        
        # Performance tips
        st.subheader("💡 Mẹo tối ưu")
        st.markdown("""
        **⚡ Chế độ Nhanh:**
        - Không sử dụng reranking
        - Phản hồi nhanh nhất
        - Phù hợp cho câu hỏi đơn giản
        
        **⚖️ Chế độ Cân bằng:**
        - Reranking có chọn lọc
        - Tốc độ và chất lượng cân bằng
        
        **🎯 Chế độ Chính xác:**
        - Reranking đầy đủ
        - Chất lượng cao nhất
        - Phù hợp cho câu hỏi phức tạp
        """)
        
        st.divider()
        
        # Quick questions
        st.subheader("❓ Câu hỏi mẫu")
        sample_questions = [
            "Thuế thu nhập cá nhân là gì?",
            "Cách tính thuế VAT như thế nào?",
            "Quy định về thuế thu nhập doanh nghiệp?",
            "Thủ tục đăng ký kinh doanh?",
            "Luật lao động quy định gì về nghỉ phép?"
        ]
        
        for question in sample_questions:
            if st.button(question, key=f"sample_{question}"):
                logger.info(f"User clicked sample question: {question}")
                # Add user message
                st.session_state.messages.append({"role": "user", "content": question})
                logger.info("Added user message to chat history")
                
                # Generate response automatically
                if st.session_state.qa_system.initialized:
                    start_time = datetime.now()
                    
                    if performance_mode == "fast":
                        retrieved_docs = st.session_state.qa_system.retrieve_and_rerank_fast(
                            question, top_k=top_k, rerank_top_k=rerank_top_k
                        )
                        context_docs = [doc["document"] for doc in retrieved_docs]
                        answer = st.session_state.qa_system.generate_answer_fast(question, context_docs)
                    else:
                        retrieved_docs = st.session_state.qa_system.retrieve_and_rerank(
                            question, top_k=top_k, rerank_top_k=rerank_top_k
                        )
                        context_docs = [doc["document"] for doc in retrieved_docs]
                        answer = st.session_state.qa_system.generate_answer(question, context_docs)
                    
                    end_time = datetime.now()
                    response_time = (end_time - start_time).total_seconds()
                    performance_info = f"⚡ Thời gian phản hồi: {response_time:.2f}s | 📄 Tài liệu: {len(retrieved_docs)} | 🎯 Chế độ: {performance_mode}"
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": answer,
                        "sources": retrieved_docs,
                        "performance_info": performance_info
                    })
                else:
                    st.session_state.messages.append({"role": "assistant", "content": "⚠️ Vui lòng khởi tạo hệ thống trước khi sử dụng."})
                
                st.rerun()
        
        st.divider()
        
        # Footer
        st.markdown("""
        <div style="text-align: center; color: #666; font-size: 0.8rem;">
            <p>⚖️ Legal QA Chatbot v2.0 - Optimized</p>
            <p>Powered by RAG + Ollama + Qdrant</p>
            <p>🚀 Enhanced Performance</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
