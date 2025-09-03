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

# LangChain imports
from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.schema import Document

dense_model_name = "sentence-transformers/all-MiniLM-L6-v2"
sparse_model_name = "Qdrant/bm25"
rerank_model_name = "jinaai/jina-reranker-v2-base-multilingual"
llm_model_name = "llama3.1:8b"

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
    """Main class for the Legal QA system."""
    
    def __init__(self):
        self.collection_name = "thue-phi-le-phi_all-MiniLM-L6-v2"
        self.client = None
        self.dense_model = None
        self.sparse_model = None
        self.rerank_model = None
        self.llm = None
        self.initialized = False
    
    def initialize(self):
        """Initialize all models and connections."""
        try:
            with st.spinner("🔄 Đang khởi tạo hệ thống..."):
                # Initialize Qdrant client
                self.client = QdrantClient(
                    host="localhost",
                    port=6333,
                    timeout=600.0
                )
                logger.info("Qdrant client initialized successfully")
                
                # Initialize embedding models
                self.dense_model = SentenceTransformer(dense_model_name)
                logger.info("Dense embedding model (SentenceTransformer) initialized")
                
                self.sparse_model = SparseTextEmbedding(sparse_model_name)
                logger.info("Sparse embedding model (FastEmbed) initialized")
                
                self.rerank_model = TextCrossEncoder(rerank_model_name)
                logger.info("Rerank model (TextCrossEncoder) initialized")
                
                # Initialize LLM
                self.llm = ChatOllama(
                    model=llm_model_name,
                    temperature=0.1,
                    top_p=0.9
                )
                logger.info("LLM (llama3.1:8b) initialized successfully")
                
                self.initialized = True
                logger.info("Full system initialization completed successfully")
                st.success("✅ Hệ thống đã sẵn sàng!")
                
        except Exception as e:
            logger.error(f"Failed to initialize full system: {str(e)}", exc_info=True)
            st.error(f"❌ Lỗi khởi tạo hệ thống: {str(e)}")
            self.initialized = False
    
    def retrieve_and_rerank(self, query: str, top_k: int = 20, rerank_top_k: int = 10) -> List[Dict]:
        """Perform hybrid retrieval and reranking."""
        logger.info(f"Starting retrieval and reranking for query: {query[:100]}...")
        logger.info(f"Parameters: top_k={top_k}, rerank_top_k={rerank_top_k}")
        
        if not self.initialized:
            return []
        
        try:
            # Generate query embeddings
            dense_vector_query = self.dense_model.encode(query)
            logger.info(f"Dense vector generated, shape: {dense_vector_query.shape}")
            
            bm25_vector_query = self.sparse_model.embed(query)
            bm25_query_vector = list(bm25_vector_query)[0]
            
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
                with_vectors=True,
                limit=top_k
            ).points
            
            logger.info(f"Retrieved {len(search_result)} documents from vector search")
            
            # Extract document texts for reranking
            initial_hits = [hit.payload["raw_context"] for hit in search_result[:rerank_top_k]]
            
            if not initial_hits:
                return []
            
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
            
            logger.info(f"Reranking completed, returning {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error in retrieve_and_rerank: {str(e)}", exc_info=True)
            return []
    
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
            
            # Create prompt template
            prompt_template = PromptTemplate(
                input_variables=["context", "question"],
                template="""
Bạn là một chuyên gia tư vấn pháp luật Việt Nam. Hãy trả lời câu hỏi dựa trên thông tin pháp lý được cung cấp.

Thông tin pháp lý:
{context}

Câu hỏi: {question}

Hướng dẫn trả lời:
1. Trả lời chính xác dựa trên thông tin được cung cấp
2. Sử dụng ngôn ngữ dễ hiểu, thân thiện
3. Nếu cần thiết, hãy giải thích thêm về các khái niệm pháp lý
4. Nếu thông tin không đủ để trả lời, hãy nói rõ điều đó
5. Luôn nhắc nhở người dùng nên tham khảo ý kiến luật sư cho các vấn đề phức tạp

Trả lời:
"""
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

def display_chat_message(role: str, content: str, sources: List[Dict] = None):
    """Display a chat message with proper styling."""
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
        
        # Initialize system button
        if st.button("🚀 Khởi tạo hệ thống", type="primary"):
            st.session_state.qa_system.initialize()
        
        # System status
        if st.session_state.qa_system.initialized:
            st.success("✅ Hệ thống đã sẵn sàng")
        else:
            st.warning("⚠️ Hệ thống chưa được khởi tạo")
        
        st.divider()
        
        # Settings
        st.subheader("🔧 Tham số tìm kiếm")
        top_k = st.slider("Số lượng tài liệu tìm kiếm", 5, 50, 20)
        rerank_top_k = st.slider("Số lượng tài liệu rerank", 3, 20, 10)
        
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
                    message.get("sources")
                )
        
        # Chat input
        if prompt := st.chat_input("Nhập câu hỏi pháp luật của bạn..."):
            logger.info(f"User entered prompt: {prompt[:100]}...")
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            display_chat_message("user", prompt)
            
            # Generate response
            if st.session_state.qa_system.initialized:
                with st.spinner("🔍 Đang tìm kiếm thông tin..."):
                    # Retrieve relevant documents
                    retrieved_docs = st.session_state.qa_system.retrieve_and_rerank(
                        prompt, top_k=top_k, rerank_top_k=rerank_top_k
                    )
                    logger.info(f"Retrieved {len(retrieved_docs)} documents")
                
                with st.spinner("🤖 Đang tạo câu trả lời..."):
                    # Generate answer
                    context_docs = [doc["document"] for doc in retrieved_docs]
                    answer = st.session_state.qa_system.generate_answer(prompt, context_docs)
                    logger.info("Generated answer successfully")
                
                # Add assistant message to chat history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": answer,
                    "sources": retrieved_docs
                })
                logger.info("Added assistant response to chat history")
                display_chat_message("assistant", answer, retrieved_docs)
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
                
            except Exception as e:
                st.error(f"Lỗi lấy thông tin: {str(e)}")
        
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
                    with st.spinner("🔍 Đang tìm kiếm thông tin..."):
                        # Retrieve relevant documents
                        retrieved_docs = st.session_state.qa_system.retrieve_and_rerank(
                            question, top_k=top_k, rerank_top_k=rerank_top_k
                        )
                        logger.info(f"Retrieved {len(retrieved_docs)} documents")
                    
                    with st.spinner("🤖 Đang tạo câu trả lời..."):
                        # Generate answer
                        context_docs = [doc["document"] for doc in retrieved_docs]
                        answer = st.session_state.qa_system.generate_answer(question, context_docs)
                        logger.info("Generated answer successfully")
                    
                    # Add assistant message to chat history
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": answer,
                        "sources": retrieved_docs
                    })
                else:
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                
                st.rerun()
        
        st.divider()
        
        # Footer
        st.markdown("""
        <div style="text-align: center; color: #666; font-size: 0.8rem;">
            <p>⚖️ Legal QA Chatbot v1.0</p>
            <p>Powered by RAG + Ollama + Qdrant</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
