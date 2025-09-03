# Legal QA Chatbot - Streamlit Application

## 🚀 Tổng quan

Ứng dụng web chatbot tư vấn pháp luật Việt Nam với 3 phiên bản:

### 📱 **3 Phiên bản ứng dụng:**
1. **`app_simple.py`** - Simple LLM Version (không cần Qdrant)
2. **`app.py`** - Full RAG Version (cần Qdrant + Ollama)


### 🔧 **Công nghệ sử dụng:**
- **RAG (Retrieval Augmented Generation)** với Qdrant vector database
- **Ollama LLM** (llama3.1:8b hoặc gemma3:1b) để tạo câu trả lời
- **Streamlit** cho giao diện web thân thiện
- **Logging system** chi tiết để debug

## 📋 Yêu cầu hệ thống

### 1. Dependencies
```bash
# Cài đặt từ pyproject.toml
uv sync
# Hoặc
pip install -e .
```

### 2. Services cần chạy (tùy phiên bản)

#### **Cho `app_simple.py` (Simple LLM):**
- ✅ **Ollama**: với model `gemma3:1b`
- ❌ **Qdrant**: Không cần

#### **Cho `app.py` (Full RAG):**
- ✅ **Qdrant Server**: `localhost:6333`
- ✅ **Ollama**: với model `llama3.1:8b`
- ✅ **Collection**: `thue-phi-le-phi_all-MiniLM-L6-v2` đã được tạo và có dữ liệu

## 🛠️ Cài đặt và chạy

### **Phương án 1: Simple LLM (Dễ nhất)**
```bash
# Bước 1: Cài đặt dependencies
uv sync

# Bước 2: Cài đặt Ollama model nhỏ
ollama pull gemma3:1b

# Bước 3: Chạy ứng dụng
streamlit run app_simple.py
```

### **Phương án 2: Full RAG (Đầy đủ tính năng)**
```bash
# Bước 1: Cài đặt dependencies
uv sync

# Bước 2: Khởi động Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Bước 3: Tạo collection và index dữ liệu
# Chạy notebook: notebooks/index_database.ipynb
# Hoặc chạy script tương tự để tạo collection

# Bước 4: Cài đặt Ollama model
ollama pull llama3.1:8b

# Bước 5: Chạy ứng dụng
streamlit run app.py
```

### **Phương án 3: Auto-start**
```bash
python start_app.py
```

## 🎯 Tính năng chính

### **So sánh 3 phiên bản:**

| Tính năng | app_simple.py | app.py |
|-----------|---------------|--------|
| **LLM Integration** | ✅ gemma3:1b | ✅ llama3.1:8b |
| **Vector Database** | ❌ Không cần | ✅ Qdrant |
| **RAG System** | ❌ Kiến thức có sẵn | ✅ Hybrid Search + Rerank |
| **Setup Complexity** | 🟢 Dễ | 🟡 Trung bình |
| **Response Quality** | 🟡 Tốt | 🟢 Rất tốt |
| **Speed** | 🟢 Nhanh | 🟡 Trung bình |

### 1. **Giao diện chat**
- Chat interface trực quan với CSS tùy chỉnh
- Hiển thị lịch sử hội thoại
- Câu hỏi mẫu click-to-use
- Status indicators và progress bars

### 2. **Hệ thống RAG (chỉ app.py)**
- **Hybrid Search**: Kết hợp dense + sparse vectors
- **Reranking**: Sắp xếp lại kết quả theo độ liên quan
- **Context-aware**: Sử dụng ngữ cảnh để tạo câu trả lời chính xác

### 3. **Tùy chỉnh tham số**
- Điều chỉnh số lượng tài liệu tìm kiếm (app.py)
- Thay đổi số lượng tài liệu rerank (app.py)
- Xem thống kê hệ thống real-time

### 4. **Nguồn tham khảo (chỉ app.py)**
- Hiển thị tài liệu gốc được sử dụng
- Điểm số độ liên quan
- Mở rộng để xem chi tiết


## 🔧 Cấu hình

### Thay đổi model LLM
Trong file `app.py`, dòng 27:
```python
dense_model_name = "sentence-transformers/all-MiniLM-L6-v2"
sparse_model_name = "Qdrant/bm25"
rerank_model_name = "jinaai/jina-reranker-v2-base-multilingual"
llm_model_name = "llama3.1:8b"
```

### Thay đổi collection Qdrant
Trong file `app.py`, dòng 30:
```python
self.collection_name = "thue-phi-le-phi_all-MiniLM-L6-v2"  # Thay đổi collection
```

## 📊 Giao diện

### Sidebar
- **Khởi tạo hệ thống**: Button để khởi tạo models
- **Tham số tìm kiếm**: Sliders để điều chỉnh
- **Lịch sử chat**: Xem và xóa lịch sử
- **Câu hỏi mẫu**: Click để sử dụng

### Main Area
- **Chat interface**: Giao diện chat chính
- **Thống kê**: Số tài liệu, tin nhắn
- **Nguồn tham khảo**: Expandable sources

## 🎨 Customization

### Thay đổi CSS
Chỉnh sửa phần CSS trong `app.py` (dòng 25-60):
```python
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;  # Thay đổi màu
        text-align: center;
    }
    # ... thêm styles khác
</style>
""", unsafe_allow_html=True)
```

### Thay đổi prompt template
Chỉnh sửa prompt trong method `generate_answer()` (dòng 150-180):
```python
prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template="""
    # Thay đổi template ở đây
    """
)
```

## 🚨 Troubleshooting

### **Lỗi thường gặp:**

#### 1. **Lỗi "Qdrant connection failed"**
```
[WinError 10061] No connection could be made because the target machine actively refused it
```
**Giải pháp:**
```bash
# Kiểm tra Qdrant server đang chạy
docker ps | grep qdrant

# Khởi động Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Kiểm tra port 6333
curl http://localhost:6333/collections
```

#### 2. **Lỗi "Collection not found"**
```
Collection `thue-phi-le-phi_all-MiniLM-L6-v2` doesn't exist!
```
**Giải pháp:**
```bash
# Chạy notebook để tạo collection
jupyter notebook notebooks/index_database.ipynb

# Hoặc kiểm tra collection có tồn tại
curl http://localhost:6333/collections
```

#### 3. **Lỗi "Ollama model not found"**
```
Model 'gemma3:1b' not found
```
**Giải pháp:**
```bash
# Kiểm tra model đã cài
ollama list

# Cài đặt model
ollama pull gemma3:1b  # cho app_simple.py
ollama pull llama3.1:8b  # cho app.py

# Khởi động Ollama server
ollama serve
```

#### 4. **Lỗi Unicode trong logging**
```
UnicodeEncodeError: 'charmap' codec can't encode character
```
**Giải pháp:**
- ✅ Đã được sửa với `encoding='utf-8'` trong file logs
- Console output vẫn có thể bị lỗi trên Windows

#### 5. **Performance issues**
**Giải pháp:**
- Giảm `top_k` và `rerank_top_k` trong sidebar
- Sử dụng `app_simple.py` thay vì `app.py`
- Sử dụng model nhỏ hơn (gemma3:1b)
- Tăng timeout trong QdrantClient

### **Debug với logs:**
```bash
# Xem logs real-time
tail -f legal_qa_simple.log
tail -f legal_qa_full.log

# Tìm lỗi
grep "ERROR" legal_qa_simple.log
grep "ERROR" legal_qa_full.log

# Theo dõi performance
grep "Generated answer length" legal_qa_simple.log
grep "Retrieved.*documents" legal_qa_full.log
```

## 📈 Monitoring

### **Logging System**
- **File logs**: `legal_qa_simple.log`, `legal_qa_full.log`
- **Console output**: Real-time với encoding UTF-8
- **Log levels**: INFO, WARNING, ERROR
- **Format**: Timestamp, module, level, message

### **Metrics được theo dõi:**
- Số lượng tài liệu trong collection (app.py)
- Số tin nhắn trong session
- Thời gian khởi tạo hệ thống
- Thời gian tạo câu trả lời
- Số lượng documents retrieved (app.py)
- Context length và answer length

### **Cách sử dụng logs:**
```bash
# Xem logs real-time
tail -f legal_qa_simple.log
tail -f legal_qa_full.log

# Tìm lỗi cụ thể
grep "ERROR" legal_qa_simple.log
grep "Failed to initialize" legal_qa_full.log

# Theo dõi performance
grep "Generated answer length" legal_qa_simple.log
grep "Retrieved.*documents" legal_qa_full.log

# Thống kê sử dụng
grep "User entered prompt" legal_qa_simple.log | wc -l
grep "User clicked" legal_qa_simple.log
```

## 🔄 Updates & Roadmap

### **Đã hoàn thành:**
- ✅ **3 phiên bản ứng dụng** (Simple LLM, Full RAG, Auto-start)
- ✅ **Logging system** chi tiết với UTF-8 encoding
- ✅ **Click-to-use sample questions** cho cả 2 phiên bản
- ✅ **Error handling** và troubleshooting guides
- ✅ **Model configuration** linh hoạt

### **Tính năng sắp tới:**
1. **Voice input**: Sử dụng `streamlit-audio-recorder`
2. **File upload**: Cho phép upload tài liệu pháp luật
3. **Export chat**: Xuất lịch sử chat ra PDF
4. **Multi-language**: Hỗ trợ tiếng Anh
5. **Admin panel**: Quản lý collection và models

### **Cải thiện performance:**
1. **Caching**: Cache embeddings và responses
2. **Async**: Sử dụng async/await cho I/O operations
3. **Batch processing**: Xử lý nhiều queries cùng lúc
4. **Model optimization**: Quantization và optimization

## 📞 Support

### **Khi gặp vấn đề:**
1. **Kiểm tra logs** trong terminal và file logs
2. **Verify services** đang chạy (Ollama, Qdrant)
3. **Test từng component** riêng biệt
4. **Check dependencies** versions
5. **Sử dụng app_simple.py** nếu app.py gặp lỗi

### **Quick Start cho người mới:**
```bash
# Cách nhanh nhất để bắt đầu
ollama pull gemma3:1b
streamlit run app_simple.py
```

### **Full Setup cho advanced users:**
```bash
# Setup đầy đủ với RAG
docker run -p 6333:6333 qdrant/qdrant
ollama pull llama3.1:8b
# Chạy notebooks/index_database.ipynb để tạo collection
streamlit run app.py
```

---

**Happy Chatting! ⚖️🤖**

*Chọn phiên bản phù hợp với nhu cầu của bạn: Simple LLM cho setup nhanh, Full RAG cho chất lượng cao!*
