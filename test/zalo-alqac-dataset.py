import json
import pandas as pd
from pathlib import Path

class DataProcessor:
    """
    Xử lý một nguồn dữ liệu bao gồm file luật (corpus) và file câu hỏi.
    """
    def __init__(self, corpus_path: str, questions_path: str, source_name: str):
        self.corpus_path = Path(corpus_path)
        self.questions_path = Path(questions_path)
        self.source_name = source_name
        self.article_lookup = {}
        self.questions = []

    def load_corpus(self):
        data = json.loads(self.corpus_path.read_text(encoding='utf-8'))
        for law in data:
            law_id = law.get('id')
            for article in law.get('articles', []):
                art_id = article.get('id')
                text = article.get('text', '')
                self.article_lookup[(law_id, art_id)] = text

    def load_questions(self):
        self.questions = json.loads(self.questions_path.read_text(encoding='utf-8'))

    def process(self) -> pd.DataFrame:
        rows = []
        for q in self.questions:
            qid = q.get('id', '')
            qtext = q.get('text', '')
            qanswer = q.get('answer', '')
            refs = q.get('relevant_articles', [])

            if refs:
                for ref in refs:
                    law_id = ref.get('law_id')
                    art_id = ref.get('article_id')
                    key = (law_id, art_id)
                    related = self.article_lookup.get(key, 'Không tìm thấy nội dung bài viết')
                    rows.append({
                        'source': self.source_name,
                        'question_id': qid,
                        'question': qtext,
                        'answer': qanswer,
                        'article_id': art_id,
                        'law_id': law_id,
                        'related_article': related
                    })
            else:
                rows.append({
                    'source': self.source_name,
                    'question_id': qid,
                    'question': qtext,
                    'answer': qanswer,
                    'article_id': None,
                    'law_id': None,
                    'related_article': 'Không tìm thấy tài liệu liên quan'
                })

        return pd.DataFrame(rows)

class MultiSourceDataProcessor:
    """
    Xử lý nhiều nguồn dữ liệu song song và lưu kết quả từng nguồn vào file riêng biệt
    theo folder 'train' hoặc 'test' dựa vào sự tồn tại của trường 'answer'.
    """
    def __init__(self, sources: list):
        self.sources = sources

    def run(self):
        for src in self.sources:
            dp = DataProcessor(src['corpus'], src['questions'], src['source'])
            dp.load_corpus()
            dp.load_questions()
            df = dp.process()

            # Kiểm tra nếu có ít nhất một câu có answer thì là train, ngược lại là test
            if any(df['answer'].astype(bool)):
                folder = 'data/processed'
            else:
                folder = 'data/final/test'

            Path(folder).mkdir(parents=True, exist_ok=True)
            output_path = f"{folder}/{src['source']}-legal.csv"
            df.to_csv(output_path, index=False)
            print(f"Saved {output_path}")

# Ví dụ sử dụng:
if __name__ == '__main__':
    sources = [
        {
            'source': 'zalo-2023',
            'corpus': 'data/raw/alqac-2023-data/additional_data/zalo/zalo_corpus.json',
            'questions': 'data/raw/alqac-2023-data/additional_data/zalo/zalo_question.json'
        },
        {
            'source': 'alqac-2022',
            'corpus': 'data/raw/alqac-2023-data/additional_data/ALQAC_2022_training_data/law.json',
            'questions': 'data/raw/alqac-2023-data/additional_data/ALQAC_2022_training_data/question.json'
        },
        {
            'source': 'alqac-2023',
            'corpus': 'data/raw/alqac-2023-data/law.json',
            'questions': 'data/raw/alqac-2023-data/train.json'
        }
    ]
    msp = MultiSourceDataProcessor(sources)
    msp.run()
