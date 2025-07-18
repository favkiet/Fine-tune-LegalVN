import json
import pandas as pd
import uuid
from datetime import datetime
import os
from typing import Dict, List, Tuple

import re

def extract_name(filepath):
    """Extract slug from json filename.
    Example: 
        - legal_qa_giao-thong-van-tai.json -> giao-thong-van-tai
    """
    filename = os.path.basename(filepath)  # Lấy phần tên file từ path
    
    # Pattern cho các định dạng file
    patterns = [
        r'^legal_qa_(.*?)(?:_output)?(?:_v\d+)?\.json$'  # Matches: legal_qa_giao-thong-van-tai.json, legal_qa_giao-thong-van-tai_output.json
    ]
    
    for pattern in patterns:
        match = re.match(pattern, filename)
        if match:
            return match.group(1)
    
    # Nếu không match với pattern nào, trả về tên file không có extension
    return os.path.splitext(filename)[0]

def generate_unique_id() -> str:
    """Tạo ID duy nhất dựa trên UUID4"""
    return str(uuid.uuid4())

def process_json_to_tables(json_file_path: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Chuyển đổi dữ liệu JSON thành các DataFrame tương ứng với cấu trúc bảng
    
    Returns:
        Tuple chứa 4 DataFrame: questions, answers, contexts, và answer_contexts
    """
    # Đọc file JSON
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Khởi tạo lists để lưu dữ liệu cho từng bảng
    questions_data = []
    answers_data = []
    contexts_data = []
    answer_contexts_data = []
    field_directory = extract_name(json_file_path)
    
    # Xử lý từng article
    for article in data:
        article_id = article['id']
        
        # Xử lý từng cặp Q&A
        for qa_pair in article['qa_pairs']:
            # Tạo question_id và thêm vào questions_data
            question_id = generate_unique_id()
            questions_data.append({
                'field_directory': field_directory,
                'question_id': question_id,
                'article_id': article_id,
                'content': qa_pair['question'],
                'created_at': article['crawled_at']
            })
            
            # Xử lý từng câu trả lời và contexts của nó
            for answer_idx, answer in enumerate(qa_pair['answers'], 1):
                # Tạo answer_id và thêm vào answers_data
                answer_id = generate_unique_id()
                answers_data.append({
                    'answer_id': answer_id,
                    'question_id': question_id,
                    'content': answer['answer'],
                    'order_index': answer_idx,
                    'created_at': article['crawled_at']
                })
                
                # Xử lý contexts của câu trả lời này
                for ctx_idx, context in enumerate(answer['contexts'], 1):
                    # Tạo context_id và thêm vào contexts_data
                    context_id = generate_unique_id()
                    contexts_data.append({
                        'context_id': context_id,
                        'content': context,
                        'created_at': article['crawled_at']
                    })
                    
                    # Thêm mối quan hệ vào answer_contexts_data
                    answer_contexts_data.append({
                        'answer_id': answer_id,
                        'context_id': context_id,
                        'order_index': ctx_idx
                    })
    
    # Chuyển đổi lists thành DataFrames
    questions_df = pd.DataFrame(questions_data)
    answers_df = pd.DataFrame(answers_data)
    contexts_df = pd.DataFrame(contexts_data)
    answer_contexts_df = pd.DataFrame(answer_contexts_data)
    
    return questions_df, answers_df, contexts_df, answer_contexts_df

def save_to_csv(output_dir: str, slug: str, *dataframes: pd.DataFrame, names: List[str]):
    """Lưu các DataFrame thành files CSV trong thư mục con của slug"""
    # Tạo thư mục con cho slug
    slug_dir = os.path.join(output_dir, slug)
    os.makedirs(slug_dir, exist_ok=True)
    
    for df, name in zip(dataframes, names):
        output_path = os.path.join(slug_dir, f'{name}.csv')
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"Saved {name} to {output_path}")

def main():
    # Đường dẫn input/output
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_file = os.path.join(root_dir, 'data', 'json', 'legal_qa_thue-phi-le-phi.json')
    output_dir = os.path.join(root_dir, 'data', 'tables')
    
    # Lấy slug từ tên file
    slug = extract_name(json_file)
    print(f"\nProcessing data for slug: {slug}")
    
    # Xử lý dữ liệu
    questions_df, answers_df, contexts_df, answer_contexts_df = process_json_to_tables(json_file)
    
    # In thống kê
    print("\nData Statistics:")
    print(f"Total questions: {len(questions_df)}")
    print(f"Total answers: {len(answers_df)}")
    print(f"Total contexts: {len(contexts_df)}")
    print(f"Total answer-context relationships: {len(answer_contexts_df)}")
    
    # Lưu kết quả vào thư mục con của slug
    save_to_csv(
        output_dir,
        slug,
        questions_df, answers_df, contexts_df, answer_contexts_df,
        names=['questions', 'answers', 'contexts', 'answer_contexts']
    )

if __name__ == '__main__':
    main() 