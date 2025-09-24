# Legal QA Chatbot - Hệ thống Tư vấn Pháp luật Việt Nam

## 🚀 Tổng quan

**Legal QA Chatbot** là một hệ thống chatbot thông minh sử dụng AI để tư vấn pháp luật Việt Nam. Hệ thống được xây dựng với công nghệ RAG (Retrieval Augmented Generation) và có thể hoạt động ở nhiều chế độ khác nhau tùy theo nhu cầu sử dụng.

### 🎯 Tính năng chính

- **🤖 Chatbot AI**: Tư vấn pháp luật tự động với độ chính xác cao
- **📚 RAG System**: Tìm kiếm và truy xuất thông tin từ cơ sở dữ liệu pháp luật
- **⚡ Đa chế độ**: Simple LLM, Full RAG, và Auto-start
- **🌐 Web Interface**: Giao diện Streamlit thân thiện và trực quan
- **📊 Monitoring**: Hệ thống logging và thống kê chi tiết
- **🔍 Hybrid Search**: Kết hợp dense và sparse vectors để tìm kiếm tối ưu

### 🏗️ Kiến trúc hệ thống

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   Qdrant DB     │    │   Ollama LLM    │
│   Web Interface │◄──►│   Vector Store  │◄──►│   Language      │
│                 │    │                 │    │   Model         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input    │    │   Document      │    │   Generated     │
│   Processing    │    │   Retrieval     │    │   Response      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Yêu cầu hệ thống

### Phần mềm cần thiết

- **Python**: >= 3.10
- **Docker**: Để chạy Qdrant vector database
- **Ollama**: Để chạy language models
- **Git**: Để clone repository

### Phần cứng khuyến nghị

- **RAM**: Tối thiểu 8GB (khuyến nghị 16GB+)
- **Storage**: Tối thiểu 10GB trống
- **CPU**: Multi-core processor

## 🛠️ Cài đặt Environment

### 1. Clone Repository

```bash
git clone <repository-url>
cd Fine-tune-LegalVN
```

### 2. Cài đặt Python Dependencies

#### Phương án A: Sử dụng uv (Khuyến nghị)

```bash
# Cài đặt uv nếu chưa có
pip install uv

# Cài đặt dependencies
uv sync
```

#### Phương án B: Sử dụng pip

```bash
# Tạo virtual environment
python -m venv venv

# Kích hoạt virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Cài đặt dependencies
pip install -e .
```

### 3. Cài đặt Ollama

#### Windows:
```bash
# Download và cài đặt từ https://ollama.ai
# Hoặc sử dụng winget
winget install Ollama.Ollama
```

#### Linux/Mac:
```bash
# Cài đặt Ollama
curl -fsSL https://ollama.ai/install.sh | sh
```

### 4. Cài đặt Docker

#### Windows:
- Download Docker Desktop từ https://docker.com
- Hoặc sử dụng winget: `winget install Docker.DockerDesktop`

#### Linux:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker
```

## 🐳 Cài đặt và Chạy Docker Services

### 1. Khởi động Qdrant Vector Database

```bash
# Chạy Qdrant container
docker run -d \
  --name qdrant-legal-qa \
  -p 6333:6333 \
  -v qdrant_storage:/qdrant/storage \
  qdrant/qdrant

# Kiểm tra Qdrant đang chạy
docker ps | grep qdrant

# Test kết nối
curl http://localhost:6333/collections
```

### 2. Cài đặt Ollama Models

```bash
# Khởi động Ollama service
ollama serve

# Cài đặt model cho Simple LLM (app_simple.py)
ollama pull gemma3:1b

# Cài đặt model cho Full RAG (app.py)
ollama pull llama3.1:8b

# Kiểm tra models đã cài
ollama list
```

### 3. Tạo Vector Database Collection

```bash
# Chạy Jupyter notebook để tạo collection
jupyter notebook notebooks/index_database.ipynb

# Hoặc chạy script Python tương tự
python scripts/setup_database.py
```

## 🚀 Hướng dẫn Chạy App

### Phương án 1: Simple LLM (Dễ nhất - Không cần Qdrant)

```bash
# Bước 1: Cài đặt model nhỏ
ollama pull gemma3:1b

# Bước 2: Chạy ứng dụng
streamlit run app_simple.py
```

**Tính năng:**
- ✅ Không cần Qdrant database
- ✅ Setup nhanh và đơn giản
- ✅ Sử dụng kiến thức có sẵn của LLM
- ⚠️ Chất lượng trả lời phụ thuộc vào training data của model

### Phương án 2: Full RAG (Đầy đủ tính năng)

```bash
# Bước 1: Khởi động Qdrant
docker run -d --name qdrant-legal-qa -p 6333:6333 qdrant/qdrant

# Bước 2: Cài đặt model lớn
ollama pull llama3.1:8b

# Bước 3: Tạo collection và index dữ liệu
# Chạy notebook: notebooks/index_database.ipynb

# Bước 4: Chạy ứng dụng
streamlit run app.py
```

**Tính năng:**
- ✅ RAG system với vector database
- ✅ Hybrid search (dense + sparse)
- ✅ Reranking để tối ưu kết quả
- ✅ Nguồn tham khảo chi tiết
- ⚠️ Setup phức tạp hơn

### Phương án 3: Auto-start (Tự động hóa)

```bash
# Chạy script tự động
python start_app.py
```

**Tính năng:**
- ✅ Tự động kiểm tra và khởi động services
- ✅ Tự động cài đặt models nếu thiếu
- ✅ Tự động start Streamlit app
- ✅ Error handling và troubleshooting


## 🎯 Cách sử dụng

### 1. Khởi tạo hệ thống

- Mở ứng dụng trong browser (thường là `http://localhost:8501`)
- Click nút **"🚀 Khởi tạo hệ thống"** trong sidebar
- Đợi hệ thống load các models (có thể mất vài phút)

### 2. Đặt câu hỏi

- Nhập câu hỏi pháp luật vào chat input
- Hoặc click vào **câu hỏi mẫu** trong sidebar
- Hệ thống sẽ tự động tìm kiếm và tạo câu trả lời

### 3. Tùy chỉnh tham số

- **Chế độ hiệu suất**: Fast, Balanced, Accurate
- **Số lượng tài liệu**: Điều chỉnh top_k và rerank_top_k
- **Cache**: Bật/tắt cache để tối ưu tốc độ

### 4. Xem nguồn tham khảo

- Click **"📚 Nguồn tham khảo"** để xem tài liệu gốc
- Kiểm tra điểm số độ liên quan
- Xem chi tiết context được sử dụng

## 🔧 Cấu hình

### Thay đổi Models

Trong file `app.py`:

```python
# Dòng 34-37
dense_model_name = "sentence-transformers/all-MiniLM-L6-v2"
sparse_model_name = "Qdrant/bm25"
rerank_model_name = "jinaai/jina-reranker-v2-base-multilingual"
llm_model_name = "llama3.1:8b"  # Thay đổi model ở đây
```

### Thay đổi Collection

```python
# Dòng 158
self.collection_name = "thue-phi-le-phi_all-MiniLM-L6-v2"
```

### Thay đổi Prompt Template

```python
# Trong method generate_answer()
prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template="""Bạn là chuyên gia tư vấn pháp luật Việt Nam...
    # Tùy chỉnh template ở đây
    """
)
```

## 🚨 Troubleshooting

### Lỗi thường gặp

#### 1. **"Qdrant connection failed"**

```bash
# Kiểm tra Qdrant đang chạy
docker ps | grep qdrant

# Khởi động Qdrant
docker run -d --name qdrant-legal-qa -p 6333:6333 qdrant/qdrant

# Test kết nối
curl http://localhost:6333/collections
```

#### 2. **"Collection not found"**

```bash
# Chạy notebook để tạo collection
jupyter notebook notebooks/index_database.ipynb

# Hoặc kiểm tra collections có sẵn
curl http://localhost:6333/collections
```

#### 3. **"Ollama model not found"**

```bash
# Kiểm tra models
ollama list

# Cài đặt model
ollama pull llama3.1:8b  # cho app.py
ollama pull gemma3:1b   # nhẹ và nhanh hơn

# Khởi động Ollama
ollama serve
```

#### 4. **Performance issues**

- Giảm `top_k` và `rerank_top_k` trong sidebar
- Sử dụng `app_simple.py` thay vì `app.py`
- Sử dụng model nhỏ hơn (gemma3:1b)
- Tăng timeout trong QdrantClient

#### 5. **Docker không chạy được**

```bash
# Windows: Khởi động Docker Desktop
# Linux: Start Docker service
sudo systemctl start docker

# Kiểm tra Docker
docker --version
docker ps
```

### Debug với Logs

```bash
# Xem logs real-time
tail -f legal_qa_full.log
tail -f legal_qa_simple.log

# Tìm lỗi
grep "ERROR" legal_qa_full.log
grep "Failed to initialize" legal_qa_full.log

# Theo dõi performance
grep "Generated answer length" legal_qa_full.log
grep "Retrieved.*documents" legal_qa_full.log
```

## 📈 Monitoring và Logs

### Logging System

- **File logs**: `legal_qa_full.log`, `legal_qa_simple.log`
- **Console output**: Real-time với UTF-8 encoding
- **Log levels**: INFO, WARNING, ERROR
- **Format**: Timestamp, module, level, message

### Metrics được theo dõi

- Số lượng tài liệu trong collection
- Số tin nhắn trong session
- Thời gian khởi tạo hệ thống
- Thời gian tạo câu trả lời
- Số lượng documents retrieved
- Context length và answer length

## 🔄 Updates & Roadmap

### Đã hoàn thành

- ✅ **3 phiên bản ứng dụng** (Simple LLM, Full RAG, Auto-start)
- ✅ **Logging system** chi tiết với UTF-8 encoding
- ✅ **Click-to-use sample questions**
- ✅ **Error handling** và troubleshooting guides
- ✅ **Model configuration** linh hoạt
- ✅ **Performance optimization** với caching

### Tính năng sắp tới

1**File upload**: Cho phép upload tài liệu pháp luật
2**Export chat**: Xuất lịch sử chat ra PDF
3**Multi-language**: Hỗ trợ tiếng Anh
4**Admin panel**: Quản lý collection và models
5**API endpoints**: REST API cho integration

### Cải thiện performance

1. **Caching**: Cache embeddings và responses
2. **Async**: Sử dụng async/await cho I/O operations
3. **Batch processing**: Xử lý nhiều queries cùng lúc
4. **Model optimization**: Quantization và optimization

## 📞 Support

### Khi gặp vấn đề

1. **Kiểm tra logs** trong terminal và file logs
2. **Verify services** đang chạy (Ollama, Qdrant)
3. **Test từng component** riêng biệt
4. **Check dependencies** versions


### Full Setup 

```bash
# Setup đầy đủ với RAG
docker run -d --name qdrant-legal-qa -p 6333:6333 qdrant/qdrant
ollama pull llama3.1:8b
# Chạy notebooks/index_database.ipynb để tạo collection
streamlit run app.py
```

## 📚 Tài liệu tham khảo

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Ollama Documentation](https://ollama.ai/docs)
- [LangChain Documentation](https://python.langchain.com/)
- [Sentence Transformers](https://www.sbert.net/)

---

**Happy Chatting! ⚖️🤖**

*Chọn phiên bản phù hợp với nhu cầu của bạn: Simple LLM cho setup nhanh, Full RAG cho chất lượng cao!*
