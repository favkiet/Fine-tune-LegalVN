import os
import pandas as pd
from pathlib import Path

# Đường dẫn tới thư mục chứa các file CSV
folder_path = Path("data/processed")

# Khởi tạo danh sách lưu thông tin từng file
summary = []

# Duyệt qua các file trong thư mục
for file_path in folder_path.glob("*.csv"):
    # Lấy kích thước file (tính bằng MB)
    size_mb = file_path.stat().st_size / (1024 * 1024)

    # Đọc file để lấy số dòng
    try:
        df = pd.read_csv(file_path)
        num_rows = len(df)
    except Exception as e:
        num_rows = "Error reading file"

    # Lưu thông tin vào danh sách
    summary.append({
        "filename": file_path.name,
        "size_mb": round(size_mb, 2),
        "num_rows": num_rows
    })

# In kết quả
for item in summary:
    print(f"File: {item['filename']}, Size: {item['size_mb']} MB, Rows: {item['num_rows']}")
