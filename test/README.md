# Unit Tests for Legal QA Project

Đây là bộ unit tests toàn diện cho dự án Legal QA, bao gồm tests cho các module chính:

## 📁 Cấu trúc Test Files

```
test/
├── README.md                    # Tài liệu hướng dẫn (file này)
├── __init__.py                 # Package initialization
├── test_runner.py              # Script chạy tests với các tùy chọn
├── test_fixtures.py            # Mock data và fixtures dùng chung
├── test_get_legal_qa_urls.py   # Tests cho URL crawler
├── test_json_to_tables.py      # Tests cho JSON to CSV converter  
├── test_legal_qa_crawler.py    # Tests cho legal QA crawler
└── coverage_html/              # HTML coverage reports (tạo tự động)
```

## 🚀 Cách chạy Tests

### Kích hoạt Virtual Environment trước khi chạy tests:

```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### Chạy tất cả tests:

```bash
python test/test_runner.py
```

### Chạy tests với verbose output:

```bash
python test/test_runner.py --verbose
```

### Chạy test cho module cụ thể:

```bash
python test/test_runner.py --module test_get_legal_qa_urls
python test/test_runner.py --module test_json_to_tables
python test/test_runner.py --module test_legal_qa_crawler
```

### Chạy tests matching pattern:

```bash
python test/test_runner.py --pattern "json"
python test/test_runner.py --pattern "crawler"
```

### Chạy tests với coverage analysis:

```bash
python test/test_runner.py --coverage
```

### Dừng ngay khi gặp lỗi đầu tiên:

```bash
python test/test_runner.py --failfast
```

### Liệt kê các test modules có sẵn:

```bash
python test/test_runner.py --list
```

### Kết hợp các tùy chọn:

```bash
python test/test_runner.py --verbose --failfast
python test/test_runner.py --pattern "json" --coverage
```

## 📊 Test Coverage

Dự án hiện có **102 unit tests** bao gồm:

- **test_get_legal_qa_urls.py**: 19 tests
  - Driver setup (Chrome/Firefox)
  - URL extraction from web pages
  - Error handling và retry logic
  - Main function execution

- **test_json_to_tables.py**: 43 tests (2 skipped)
  - Data validation và cleaning
  - JSON parsing và processing
  - DataFrame conversion
  - CSV export functionality
  - File naming patterns

- **test_legal_qa_crawler.py**: 40 tests
  - Text processing utilities
  - HTML parsing (tables, paragraphs, blockquotes)
  - QA pair extraction
  - Scrapy crawler functionality

- **test_fixtures.py**: 0 tests (chỉ chứa mock data)

## 🧪 Test Categories

### 1. Unit Tests
- Test từng function/method riêng lẻ
- Mock external dependencies
- Validate input/output behavior

### 2. Integration Tests
- Test workflow hoàn chỉnh
- File I/O operations
- Error propagation

### 3. Mock Tests
- Mock WebDriver operations
- Mock file system operations
- Mock network requests

## 📋 Test Results Summary

Kết quả chạy tests gần nhất:

```
Overall Test Summary:
════════════════════════════════════════════════════════════
Total Modules:    4
Modules Passed:   4
Modules Failed:   0
Total Duration:   10.36s

Module Results:
  ✓ test_fixtures                  (0.08s)
  ✓ test_get_legal_qa_urls         (9.40s)
  ✓ test_json_to_tables            (0.49s)
  ✓ test_legal_qa_crawler          (0.39s)

🎉 ALL MODULES PASSED! 🎉
```

## 🔧 Dependencies

Tests yêu cầu các packages sau (đã có trong virtual environment):

```python
# Core testing
unittest (built-in)
unittest.mock (built-in)

# Data processing
pandas
json (built-in)
pathlib (built-in)

# Web scraping (for mocking)
selenium
scrapy

# Optional: Coverage analysis
coverage  # pip install coverage
```

## 💡 Tips cho Developers

### 1. Chạy tests thường xuyên:
```bash
# Quick test trước khi commit
python test/test_runner.py --failfast

# Full test suite
python test/test_runner.py --coverage
```

### 2. Debug tests cụ thể:
```bash
# Chạy chỉ test bị lỗi
python test/test_runner.py --module test_json_to_tables --verbose
```

### 3. Thêm tests mới:
- Tạo test methods trong file tương ứng
- Sử dụng fixtures từ `test_fixtures.py`
- Follow naming convention: `test_<functionality>`

### 4. Mock best practices:
- Sử dụng `@patch` decorator
- Mock ở level thấp nhất cần thiết
- Verify mock calls với `assert_called_with()`

## 🐛 Known Issues

1. **Complex Path Mocking**: 2 tests bị skip do path mocking phức tạp
2. **WebDriver Tests**: Mất thời gian (~9s) do sleep trong retry logic
3. **Coverage Integration**: Cần install `coverage` package riêng

## 🚀 Future Improvements

1. **Performance**: Optimize WebDriver mock tests
2. **Coverage**: Aim for >95% code coverage
3. **Integration**: Add end-to-end workflow tests
4. **CI/CD**: Integrate với GitHub Actions
5. **Fixtures**: Mở rộng test fixtures cho edge cases

## 📞 Support

Nếu gặp vấn đề với tests:

1. Đảm bảo virtual environment được activate
2. Check Python version compatibility (3.10+)
3. Verify all dependencies installed
4. Run `python test/test_runner.py --list` để check test discovery

---

**Happy Testing! 🧪✨**
