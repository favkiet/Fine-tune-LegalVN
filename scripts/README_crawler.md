# Hướng dẫn sử dụng Legal QA URL Crawler

## 🚀 Cách sử dụng

### 1. Chạy với Chrome (mặc định)
```bash
python get_legal_qa_urls.py
```

### 2. Chạy với Firefox
```bash
python get_legal_qa_urls.py --browser firefox
```

### 3. Tùy chỉnh URL và số trang
```bash
# Crawl chủ đề khác
python get_legal_qa_urls.py --url "https://thuvienphapluat.vn/hoi-dap-phap-luat/giao-thong-van-tai"

# Giới hạn số trang
python get_legal_qa_urls.py --max-pages 10

# Kết hợp các tùy chọn
python get_legal_qa_urls.py --browser firefox --url "https://thuvienphapluat.vn/hoi-dap-phap-luat/lao-dong" --max-pages 5
```

## 📋 Các tham số

| Tham số | Mặc định | Mô tả |
|---------|----------|-------|
| `--browser` | `chrome` | Browser để sử dụng: `chrome` hoặc `firefox` |
| `--url` | `https://thuvienphapluat.vn/hoi-dap-phap-luat/thue-phi-le-phi` | URL gốc để crawl |
| `--max-pages` | `25` | Số trang tối đa để crawl |

## 📁 Kết quả

Script sẽ tạo file JSON trong thư mục `data/json/` với tên:
```
legal_qa_{slug}_urls.json
```

Ví dụ: `legal_qa_thue-phi-le-phi_urls.json`

## 🔧 Yêu cầu hệ thống

### Chrome (khuyến nghị)
- Chrome browser đã cài đặt
- Tự động download ChromeDriver

### Firefox
- Firefox browser đã cài đặt
- Tự động download GeckoDriver

## ⚠️ Lưu ý

1. **Chrome** là lựa chọn mặc định vì ổn định hơn trên Windows
2. **Firefox** có thể gặp vấn đề nếu không cài đặt đúng cách
3. Script chạy ở chế độ **headless** (không hiển thị browser)
4. Tự động tạo thư mục `data/json/` nếu chưa có

## 🐛 Xử lý lỗi

Nếu gặp lỗi với Firefox:
```bash
# Thử với Chrome
python get_legal_qa_urls.py --browser chrome
```

Nếu gặp lỗi với Chrome:
```bash
# Thử với Firefox
python get_legal_qa_urls.py --browser firefox
```
