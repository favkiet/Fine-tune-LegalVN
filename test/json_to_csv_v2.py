import json
import csv
import logging
from pathlib import Path
from typing import List, Dict

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_qa_pair(qa_pair: Dict) -> bool:
    """Kiểm tra tính hợp lệ của cặp Q&A"""
    required_fields = ['id', 'question', 'answer']
    
    # Kiểm tra các trường bắt buộc
    if not all(field in qa_pair for field in required_fields):
        return False
        
    # Kiểm tra nội dung không trống
    if not qa_pair['question'].strip() or not qa_pair['answer'].strip():
        return False
        
    return True

def convert_json_to_csv(json_file: str, csv_file: str):
    try:
        # Đọc file JSON
        logger.info(f"Reading JSON file: {json_file}")
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Kiểm tra dữ liệu
        if not isinstance(data, list):
            logger.error("JSON data must be a list of QA pairs")
            return
            
        # Đếm số cặp Q&A hợp lệ
        valid_pairs = [pair for pair in data if validate_qa_pair(pair)]
        logger.info(f"Found {len(valid_pairs)} valid QA pairs out of {len(data)} total items")
        
        # Tạo file CSV
        logger.info(f"Creating CSV file: {csv_file}")
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # Ghi header với các trường từ format mới
            headers = ['id', 'question', 'answer', 'context', 'url', 'title', 'source', 'crawled_at']
            writer.writerow(headers)
            
            # Ghi dữ liệu
            for qa_pair in valid_pairs:
                row = [
                    qa_pair.get('id', ''),
                    qa_pair.get('question', ''),
                    qa_pair.get('answer', ''),
                    qa_pair.get('context', ''),
                    qa_pair.get('url', ''),
                    qa_pair.get('title', ''),
                    qa_pair.get('source', ''),
                    qa_pair.get('crawled_at', '')
                ]
                writer.writerow(row)
        
        logger.info(f"Successfully converted {len(valid_pairs)} QA pairs to CSV")
        
        # Hiển thị thống kê
        logger.info("Statistics:")
        logger.info(f"- Total items in JSON: {len(data)}")
        logger.info(f"- Valid QA pairs: {len(valid_pairs)}")
        logger.info(f"- Invalid/skipped pairs: {len(data) - len(valid_pairs)}")
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {str(e)}")
    except Exception as e:
        logger.error(f"Error converting JSON to CSV: {str(e)}")
        raise

def main():
    # Đường dẫn file
    root_dir = Path(__file__).parent.parent
    json_file = root_dir / 'data' / 'json' / 'qa-tien-te-ngan-hang_v2.json'
    csv_file = root_dir / 'data' / 'processed' / 'qa-tien-te-ngan-hang_v2.csv'
    
    # Tạo thư mục nếu chưa tồn tại
    csv_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Kiểm tra file JSON tồn tại
    if not json_file.exists():
        logger.error(f"JSON file not found: {json_file}")
        return
    
    try:
        convert_json_to_csv(str(json_file), str(csv_file))
    except Exception as e:
        logger.error(f"Failed to convert file: {str(e)}")

if __name__ == '__main__':
    main() 