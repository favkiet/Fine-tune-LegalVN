"""
Simple Legal QA Chatbot with LLM - Streamlit Application
Simplified version using LLM but without Qdrant vector database
"""

import streamlit as st
import pandas as pd
from typing import List, Dict
import logging

# LangChain imports for LLM
from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('legal_qa_simple.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Legal QA Chatbot - Simple LLM",
    page_icon="⚖️",
    layout="wide"
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
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .status-ready {
        background-color: #4caf50;
    }
    .status-not-ready {
        background-color: #f44336;
    }
</style>
""", unsafe_allow_html=True)

class SimpleLegalQAWithLLM:
    """Simple Legal QA system using LLM without vector database."""
    
    def __init__(self):
        self.initialized = False
        self.llm = None
        self.legal_knowledge = {
            "thuế thu nhập cá nhân": """
            Thuế thu nhập cá nhân (TNCN) là loại thuế trực thu đánh vào thu nhập của cá nhân.
            
            Đối tượng chịu thuế:
            - Cá nhân cư trú: Thu nhập phát sinh trong và ngoài lãnh thổ Việt Nam
            - Cá nhân không cư trú: Thu nhập phát sinh trong lãnh thổ Việt Nam
            
            Thu nhập chịu thuế bao gồm: thu nhập từ kinh doanh, tiền lương, đầu tư vốn, 
            chuyển nhượng vốn, chuyển nhượng bất động sản, trúng thưởng, bản quyền, 
            nhượng quyền thương mại, thừa kế, quà tặng.
            
            Mức thuế suất từ 5% đến 35% tùy theo mức thu nhập.
            """,
            
            "thuế vat": """
            Thuế giá trị gia tăng (VAT) là loại thuế gián thu đánh vào giá trị tăng thêm của hàng hóa, dịch vụ.
            
            Đối tượng chịu thuế: Hàng hóa, dịch vụ sử dụng cho sản xuất, kinh doanh và tiêu dùng ở Việt Nam.
            
            Mức thuế suất:
            - 0%: Hàng hóa, dịch vụ xuất khẩu
            - 5%: Hàng hóa, dịch vụ thiết yếu
            - 10%: Hàng hóa, dịch vụ thông thường
            - 8%: Một số hàng hóa, dịch vụ đặc biệt
            
            Cách tính: Thuế VAT phải nộp = Thuế VAT đầu ra - Thuế VAT đầu vào được khấu trừ
            """,
            
            "luật lao động": """
            Luật Lao động quy định về quyền và nghĩa vụ của người lao động và người sử dụng lao động.
            
            Quyền của người lao động: Làm việc, tự do lựa chọn việc làm, được trả lương đầy đủ, 
            nghỉ ngơi, nghỉ phép năm, an toàn lao động, tham gia bảo hiểm xã hội.
            
            Nghĩa vụ: Thực hiện công việc theo hợp đồng, tuân thủ nội quy, bảo vệ tài sản doanh nghiệp.
            
            Thời gian làm việc: Không quá 8 giờ/ngày, 48 giờ/tuần, nghỉ giữa ca ít nhất 30 phút.
            """,
            
            "đăng ký kinh doanh": """
            Thủ tục đăng ký kinh doanh:
            
            1. Chuẩn bị hồ sơ: Đơn đề nghị, điều lệ công ty, danh sách thành viên/cổ đông, 
               bản sao CMND/CCCD của người đại diện.
            
            2. Nộp hồ sơ: Trực tiếp tại Phòng Đăng ký kinh doanh hoặc qua mạng.
            
            3. Thời gian xử lý: 3-5 ngày làm việc.
            
            4. Lệ phí: 200.000 VNĐ (DNTN) hoặc 300.000 VNĐ (TNHH, cổ phần).
            
            5. Sau khi cấp phép: Khắc dấu, đăng ký thuế, mở tài khoản ngân hàng.
            """,
            
            "hợp đồng lao động": """
            Hợp đồng lao động là thỏa thuận giữa người lao động và người sử dụng lao động về việc làm có trả công.
            
            Các loại hợp đồng:
            - Hợp đồng không xác định thời hạn
            - Hợp đồng xác định thời hạn (không quá 36 tháng)
            - Hợp đồng theo mùa vụ hoặc theo một công việc nhất định (không quá 12 tháng)
            
            Nội dung bắt buộc: Công việc, địa điểm làm việc, thời hạn hợp đồng, mức lương, 
            thời gian làm việc, nghỉ ngơi, bảo hiểm xã hội.
            """,
            
            "nghỉ việc": """
            Quy định về nghỉ việc:
            
            Người lao động có quyền đơn phương chấm dứt hợp đồng lao động khi:
            - Không được bố trí đúng công việc, địa điểm làm việc
            - Không được trả lương đầy đủ, đúng thời hạn
            - Bị ngược đãi, quấy rối tình dục, cưỡng bức lao động
            
            Thời báo trước: 45 ngày (hợp đồng không xác định thời hạn), 30 ngày (hợp đồng xác định thời hạn).
            
            Người sử dụng lao động phải trả lương, bảo hiểm xã hội và các quyền lợi khác.
            """
        }
    
    def initialize(self):
        """Initialize the LLM system."""
        try:
            with st.spinner("🔄 Đang khởi tạo LLM..."):
                logger.info("Initializing ChatOllama with model: gemma3:1b")
                # Initialize LLM with a smaller model for faster response
                self.llm = ChatOllama(
                    model="gemma3:1b",  # Smaller model for faster response
                    temperature=0.1,
                    top_p=0.9
                )
                self.initialized = True
                logger.info("LLM system initialized successfully")
                return True
        except Exception as e:
            logger.error(f"Failed to initialize LLM system: {str(e)}")
            st.error(f"❌ Lỗi khởi tạo LLM: {str(e)}")
            self.initialized = False
            return False
    
    def get_relevant_knowledge(self, question: str) -> str:
        """Get relevant legal knowledge based on question keywords."""
        logger.info(f"Getting relevant knowledge for question: {question[:50]}...")
        question_lower = question.lower()
        relevant_knowledge = []
        matched_topics = []
        
        for topic, knowledge in self.legal_knowledge.items():
            if any(keyword in question_lower for keyword in topic.split()):
                relevant_knowledge.append(knowledge)
                matched_topics.append(topic)
        
        # If no specific topic found, return general legal knowledge
        if not relevant_knowledge:
            relevant_knowledge = list(self.legal_knowledge.values())[:2]  # First 2 topics
            logger.info("No specific topic matched, using general knowledge")
        else:
            logger.info(f"Matched topics: {matched_topics}")
        
        logger.info(f"Retrieved {len(relevant_knowledge)} knowledge chunks")
        return "\n\n".join(relevant_knowledge)
    
    def get_answer(self, question: str) -> str:
        """Get answer using LLM with legal knowledge context."""
        logger.info(f"Processing question: {question[:100]}...")
        
        if not self.initialized:
            logger.warning("System not initialized, returning error message")
            return "Hệ thống chưa được khởi tạo. Vui lòng nhấn 'Khởi tạo hệ thống'."
        
        try:
            # Get relevant legal knowledge
            context = self.get_relevant_knowledge(question)
            logger.info(f"Context length: {len(context)} characters")
            
            # Create prompt template
            prompt_template = PromptTemplate(
                input_variables=["context", "question"],
                template="""
Bạn là một chuyên gia tư vấn pháp luật Việt Nam. Hãy trả lời câu hỏi dựa trên kiến thức pháp lý được cung cấp.

Kiến thức pháp lý:
{context}

Câu hỏi: {question}

Hướng dẫn trả lời:
1. Trả lời chính xác dựa trên kiến thức được cung cấp
2. Sử dụng ngôn ngữ dễ hiểu, thân thiện
3. Nếu cần thiết, hãy giải thích thêm về các khái niệm pháp lý
4. Nếu thông tin không đủ để trả lời, hãy nói rõ điều đó
5. Luôn nhắc nhở người dùng nên tham khảo ý kiến luật sư cho các vấn đề phức tạp
6. Trả lời ngắn gọn, súc tích (không quá 300 từ)

Trả lời:
"""
            )
            
            # Create chain
            chain = prompt_template | self.llm | StrOutputParser()
            
            # Generate answer
            answer = chain.invoke({"context": context, "question": question})
            logger.info(f"Generated answer length: {len(answer)} characters")
            logger.info("Answer generation completed successfully")
            return answer
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}", exc_info=True)
            return f"Xin lỗi, có lỗi xảy ra khi tạo câu trả lời: {str(e)}"

def initialize_session_state():
    """Initialize session state."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
        logger.info("Created new messages list in session state")
    if "qa_system" not in st.session_state:
        st.session_state.qa_system = SimpleLegalQAWithLLM()
        logger.info("Created new QA system in session state")

def display_message(role: str, content: str):
    """Display a chat message."""
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

def main():
    """Main application."""
    
    # Initialize
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">⚖️ Legal QA Chatbot - Simple LLM</h1>', unsafe_allow_html=True)
    st.markdown("### Phiên bản đơn giản sử dụng LLM (không cần Qdrant)")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Cài đặt")
        
        # System status
        status_color = "status-ready" if st.session_state.qa_system.initialized else "status-not-ready"
        status_text = "Sẵn sàng" if st.session_state.qa_system.initialized else "Chưa sẵn sàng"
        status_icon = "✅" if st.session_state.qa_system.initialized else "⚠️"
        
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 1rem; padding: 0.5rem; border-radius: 0.5rem; background-color: {'#e8f5e8' if st.session_state.qa_system.initialized else '#fff3cd'};">
            <span class="status-indicator {status_color}"></span>
            <strong>{status_icon} Trạng thái: {status_text}</strong>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Khởi tạo hệ thống", type="primary"):
            if st.session_state.qa_system.initialize():
                st.success("✅ Hệ thống đã sẵn sàng!")
                logger.info("System initialization completed successfully")
                st.rerun()
            else:
                logger.error("System initialization failed")
        
        # Show instruction if not initialized
        if not st.session_state.qa_system.initialized:
            st.warning("""
            **Hướng dẫn:**
            1. Nhấn "🚀 Khởi tạo hệ thống" để bắt đầu
            2. Đảm bảo Ollama đang chạy với model `gemma3:1b`
            3. Sau khi khởi tạo, bạn có thể đặt câu hỏi
            """)
        
        st.divider()
        
        # Model info
        st.subheader("🤖 Thông tin LLM")
        st.info("""
        **Model:** gemma3:1b
        **Tính năng:** 
        - Sử dụng LLM để tạo câu trả lời
        - Không cần Qdrant vector database
        - Phản hồi nhanh hơn
        - Kiến thức pháp lý có sẵn
        """)
        
        st.divider()
        
        # Quick questions
        st.subheader("❓ Câu hỏi mẫu")
        sample_questions = [
            "Thuế thu nhập cá nhân là gì?",
            "Cách tính thuế VAT như thế nào?",
            "Luật lao động quy định gì?",
            "Thủ tục đăng ký kinh doanh?",
            "Quyền của người lao động?",
            "Hợp đồng lao động có những loại nào?",
            "Quy định về nghỉ việc?"
        ]
        
        for question in sample_questions:
            if st.button(question, key=f"sample_{question}"):
                logger.info(f"User clicked sample question: {question}")
                # Add user message
                st.session_state.messages.append({"role": "user", "content": question})
                
                # Generate response automatically
                if st.session_state.qa_system.initialized:
                    with st.spinner("🤖 Đang tạo câu trả lời..."):
                        answer = st.session_state.qa_system.get_answer(question)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    error_msg = "⚠️ Vui lòng khởi tạo hệ thống trước."
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                
                st.rerun()
        
        st.divider()
        
        if st.button("🗑️ Xóa lịch sử"):
            st.session_state.messages = []
            logger.info("Cleared chat history")
            st.rerun()
    
    # Main chat
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Display messages
        for message in st.session_state.messages:
            display_message(message["role"], message["content"])
        
        # Chat input
        if prompt := st.chat_input("Nhập câu hỏi pháp luật..."):
            logger.info(f"User entered prompt: {prompt[:100]}...")
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            display_message("user", prompt)
            
            # Generate response
            if st.session_state.qa_system.initialized:
                with st.spinner("🤖 Đang tạo câu trả lời..."):
                    answer = st.session_state.qa_system.get_answer(prompt)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                display_message("assistant", answer)
            else:
                error_msg = "⚠️ Vui lòng khởi tạo hệ thống trước khi sử dụng."
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                display_message("assistant", error_msg)
    
    with col2:
        st.subheader("📊 Thống kê")
        st.metric("💬 Số tin nhắn", len(st.session_state.messages))
        
        if st.session_state.qa_system.initialized:
            st.metric("🤖 LLM Model", "gemma3:1b")
        
        st.divider()
        
        st.subheader("ℹ️ Thông tin")
        st.info("""
        **Phiên bản Simple LLM** này:
        - ✅ Sử dụng LLM (gemma3:1b)
        - ✅ Kiến thức pháp lý có sẵn
        - ❌ Không cần Qdrant
        - ❌ Không cần vector database
        - ⚡ Phản hồi nhanh
        
        **So sánh:**
        - `app_simple.py`: Chỉ keyword matching
        - `app_simple_llm.py`: LLM + kiến thức có sẵn
        - `app.py`: LLM + RAG + Qdrant
        """)
        
        st.divider()
        
        st.markdown("""
        <div style="text-align: center; color: #666; font-size: 0.8rem;">
            <p>⚖️ Legal QA Chatbot v1.0</p>
            <p>Simple LLM Version</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
