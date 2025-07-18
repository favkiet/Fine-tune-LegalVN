### Logic thu thập dữ liệu từ website
1. thẻ `<h2></h2>` là câu hỏi
2. thẻ `<p></p>` là câu trả lời
3. thẻ `<blockquote></blockquote>` là ngữ cảnh
4. thẻ `<table></table>` là bảng
5. Cấu trúc của 1 sample trên website
    ```html
    <h2>Câu hỏi</h2>
    <p>Câu trả lời </p>
    <p>Câu trả lời </p>
    ...
    <table> ngữ cảnh bảng </table> (//*[@id="news-content"]/table)
    <blockquote> Ngữ cảnh</blockquote>
    <blockquote> Ngữ cảnh</blockquote>
    ...
    <p>Câu trả lời </p>
    <p>Câu trả lời </p>
    ...
    ```
    Kết qủa nên lưu theo cấu trúc từ trên xuống:
    ```json
    [
        {
            "url":
            "qa_pairs": [
                {
                    "question": <h2></h2>,
                    "answer_1": <p> Câu trả lời 1</p>,
                    "context_1": <blockquote> Ngữ cảnh 1 </blockquote>,
                    "context_2": <blockquote> Ngữ cảnh 2 </blockquote>,
                    "context_3": <blockquote> Ngữ cảnh 3 </blockquote>,
                    ...
                    "answer_2": <p> Câu trả lời 1</p>,
                    "context_1": <blockquote> Ngữ cảnh 1 </blockquote>,
                    "context_2": <blockquote> Ngữ cảnh 2 </blockquote>,
                    "context_3": <blockquote> Ngữ cảnh 3 </blockquote>,
                    ...
                    "answer_n": <p> Câu trả lời n </p>
                } (Nếu sau mỗi <p> có không hoặc nhiều <blockquote>)
            ]
        }
    ]
    ```

### Mô tả table và database

Hệ thống cơ sở dữ liệu bao gồm 4 bảng chính:

1. **Bảng Questions (questions.csv)**
   - `question_id`: UUID - Định danh duy nhất cho mỗi câu hỏi
   - `content`: Text - Nội dung câu hỏi
   - `created_at`: Timestamp - Thời điểm tạo câu hỏi

2. **Bảng Answers (answers.csv)**
   - `answer_id`: UUID - Định danh duy nhất cho mỗi câu trả lời
   - `question_id`: UUID - Khóa ngoại liên kết với bảng Questions
   - `content`: Text - Nội dung câu trả lời
   - `order_index`: Integer - Thứ tự của câu trả lời trong một câu hỏi
   - `created_at`: Timestamp - Thời điểm tạo câu trả lời

3. **Bảng Contexts (contexts.csv)**
   - `context_id`: UUID - Định danh duy nhất cho mỗi ngữ cảnh
   - `content`: Text - Nội dung ngữ cảnh
   - `created_at`: Timestamp - Thời điểm tạo ngữ cảnh

4. **Bảng Answer_Contexts (answer_contexts.csv)**
   - `answer_id`: UUID - Khóa ngoại liên kết với bảng Answers
   - `context_id`: UUID - Khóa ngoại liên kết với bảng Contexts
   - `order_index`: Integer - Thứ tự của ngữ cảnh trong một câu trả lời

Mối quan hệ giữa các bảng:
- Một câu hỏi (Question) có thể có nhiều câu trả lời (Answers)
- Một câu trả lời (Answer) có thể có nhiều ngữ cảnh (Contexts)
- Mối quan hệ giữa Answer và Context được quản lý thông qua bảng trung gian Answer_Contexts

Đặc điểm:
- Sử dụng UUID để định danh duy nhất các bản ghi
- Có trường order_index để duy trì thứ tự của câu trả lời và ngữ cảnh
- Thời gian được lưu dưới dạng timestamp với múi giờ
- Các khóa ngoại được sử dụng để đảm bảo tính toàn vẹn dữ liệu

### Tiền xử lý dữ liệu
1. Loại bỏ `"[....]"`, `[...]`
2. Loai bỏ các câu hỏi liên quan đến mẫu văn bản (cần file doc, pdf hoặc ảnh): `Hình từ Internet`
3.   