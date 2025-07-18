import pandas as pd
import json
from typing import Dict, List
import os
from datetime import datetime

def load_dataframes() -> tuple:
    """Load all CSV files into pandas DataFrames"""
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'tables')
    
    questions_df = pd.read_csv(os.path.join(base_dir, 'questions.csv'))
    answers_df = pd.read_csv(os.path.join(base_dir, 'answers.csv'))
    contexts_df = pd.read_csv(os.path.join(base_dir, 'contexts.csv'))
    answer_contexts_df = pd.read_csv(os.path.join(base_dir, 'answer_contexts.csv'))
    
    return questions_df, answers_df, contexts_df, answer_contexts_df

def print_qa_sample(
    questions_df: pd.DataFrame,
    answers_df: pd.DataFrame,
    contexts_df: pd.DataFrame,
    answer_contexts_df: pd.DataFrame,
    article_id: str = None
) -> None:
    """
    In mẫu Q&A theo format:
    Câu hỏi
    Câu trả lời
    Ngữ cảnh
    Câu trả lời
    Ngữ cảnh
    ...
    """
    # Nếu không có article_id, lấy article đầu tiên
    if article_id is None:
        article_id = questions_df['article_id'].iloc[0]
    
    # Lấy tất cả câu hỏi của article
    article_questions = questions_df[questions_df['article_id'] == article_id]
    
    # Chọn ngẫu nhiên 1 câu hỏi
    random_question = article_questions.sample(n=1).iloc[0]
    
    print("\n" + "="*100)
    print(f"Article ID: {article_id}")
    print("="*100)
    
    print(f"\nCÂU HỎI:")
    print("-"*100)
    print(random_question['content'])
    print("-"*100)
    
    # Lấy tất cả câu trả lời của câu hỏi này, sắp xếp theo order_index
    question_answers = answers_df[
        answers_df['question_id'] == random_question['question_id']
    ].sort_values('order_index')
    
    for ans_idx, answer in question_answers.iterrows():
        print(f"\nCâu trả lời {ans_idx + 1}:")
        print(answer['content'])
        
        # Lấy tất cả contexts của câu trả lời này
        answer_context_ids = answer_contexts_df[
            answer_contexts_df['answer_id'] == answer['answer_id']
        ].sort_values('order_index')['context_id']
        
        # Lấy nội dung của các contexts
        contexts = contexts_df[
            contexts_df['context_id'].isin(answer_context_ids)
        ]['content'].tolist()
        
        if contexts:
            print("\nNgữ cảnh:")
            for ctx_idx, context in enumerate(contexts, 1):
                print(f"{ctx_idx}. {context}")
        
        print("-"*50)

def find_article_with_contexts(
    questions_df: pd.DataFrame,
    answers_df: pd.DataFrame,
    answer_contexts_df: pd.DataFrame
) -> str:
    """Tìm một article có contexts để làm mẫu"""
    # Lấy các answer_id có contexts
    answers_with_contexts = answer_contexts_df['answer_id'].unique()
    
    # Lấy các câu trả lời có contexts
    answers_df_with_contexts = answers_df[
        answers_df['answer_id'].isin(answers_with_contexts)
    ]
    
    # Lấy các câu hỏi có câu trả lời với contexts
    questions_with_contexts = questions_df[
        questions_df['question_id'].isin(answers_df_with_contexts['question_id'])
    ]
    
    # Trả về article_id đầu tiên có contexts
    return questions_with_contexts['article_id'].iloc[0]

def main():
    # Load data
    questions_df, answers_df, contexts_df, answer_contexts_df = load_dataframes()
    
    # In thống kê
    print("\nData Statistics:")
    print(f"Total articles: {questions_df['article_id'].nunique()}")
    print(f"Total questions: {len(questions_df)}")
    print(f"Total answers: {len(answers_df)}")
    print(f"Total contexts: {len(contexts_df)}")
    print(f"Total answer-context relationships: {len(answer_contexts_df)}")
    
    # Tìm một article có contexts
    article_id = find_article_with_contexts(questions_df, answers_df, answer_contexts_df)
    
    # In mẫu Q&A theo format yêu cầu
    print_qa_sample(
        questions_df, answers_df, contexts_df, answer_contexts_df,
        article_id=article_id
    )

if __name__ == '__main__':
    main() 