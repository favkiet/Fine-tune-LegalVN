import json
import csv
import logging
from pathlib import Path

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def convert_json_to_csv(json_file, csv_file):
    try:
        # Đọc file JSON
        logger.info(f"Reading JSON file: {json_file}")
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Tạo file CSV
        logger.info(f"Creating CSV file: {csv_file}")
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # Ghi header
            writer.writerow(['url', 'question', 'answer'])
            
            # Đếm số dòng đã xử lý
            total_rows = 0
            
            # Ghi dữ liệu
            for item in data:
                url = item['url']
                
                # Với mỗi cặp Q&A trong bài viết
                for qa_pair in item['qa_pairs']:
                    question = qa_pair['question']
                    # Ghép các câu trả lời thành một đoạn văn
                    answer = ' '.join(qa_pair['answers'])
                    
                    writer.writerow([url, question, answer])
                    total_rows += 1
        
        logger.info(f"Successfully converted {len(data)} articles into {total_rows} QA pairs")
        
    except Exception as e:
        logger.error(f"Error converting JSON to CSV: {str(e)}")
        raise

def main():
    # Đường dẫn file
    json_file = 'data/json/qa-tien-te-ngan-hang.json'
    csv_file = 'data/raw/qa-tien-te-ngan-hang.csv'
    
    # Tạo thư mục nếu chưa tồn tại
    Path(csv_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Kiểm tra file JSON tồn tại
    if not Path(json_file).exists():
        logger.error(f"JSON file not found: {json_file}")
        return
    
    try:
        convert_json_to_csv(json_file, csv_file)
    except Exception as e:
        logger.error(f"Failed to convert file: {str(e)}")

if __name__ == '__main__':
    main() 