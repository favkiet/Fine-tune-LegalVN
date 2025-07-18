import scrapy
from scrapy.crawler import CrawlerProcess
import json
import logging
import os
from typing import List, Dict, Optional
from datetime import datetime

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LegalQACrawlerV2(scrapy.Spider):
    name = 'legal_qa_v2'
    
    def __init__(self, *args, **kwargs):
        super(LegalQACrawlerV2, self).__init__(*args, **kwargs)
        # Lấy đường dẫn tuyệt đối của thư mục gốc
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Đọc URLs từ file JSON
        try:
            urls_file = os.path.join(self.root_dir, 'data', 'json', 'legal_qa_urls.json')
            logger.info(f"Reading URLs from: {urls_file}")
            
            with open(urls_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.start_urls = [item['url'] for item in data]
                logger.info(f"Loaded {len(self.start_urls)} URLs to crawl")
                logger.info(f"URLs to crawl: {self.start_urls}")
        except Exception as e:
            logger.error(f"Error loading URLs: {str(e)}")
            self.start_urls = []

    def clean_text(self, text: Optional[str]) -> Optional[str]:
        """Làm sạch văn bản, giữ lại cấu trúc và định dạng quan trọng"""
        if not text:
            return None
        
        # Loại bỏ khoảng trắng dư thừa nhưng giữ cấu trúc
        lines = text.split('\n')
        cleaned_lines = [' '.join(line.split()) for line in lines if line.strip()]
        return ' '.join(cleaned_lines)

    def extract_qa_context(self, question_element) -> Dict:
        """Trích xuất câu hỏi, câu trả lời và ngữ cảnh từ một phần tử h2"""
        qa_data = {
            'question': '',
            'answer': '',
            'context': ''
        }
        
        # Lấy nội dung câu hỏi
        qa_data['question'] = self.clean_text(question_element.xpath('string()').get())
        logger.debug(f"Extracted question: {qa_data['question']}")
        
        # Lấy tất cả các phần tử sau h2 cho đến h2 tiếp theo
        answer_parts = []
        context_parts = []
        current_element = question_element.xpath('following-sibling::*')
        
        for element in current_element:
            element_type = element.xpath('name()').get()
            
            # Dừng nếu gặp h2 tiếp theo
            if element_type == 'h2':
                break
            
            # Xử lý phần tử p là câu trả lời
            if element_type == 'p':
                text = self.clean_text(element.xpath('string()').get())
                if text:
                    answer_parts.append(text)
                    logger.debug(f"Found answer part: {text[:100]}...")
            
            # Xử lý phần tử blockquote là ngữ cảnh
            elif element_type == 'blockquote':
                text = self.clean_text(element.xpath('string()').get())
                if text:
                    context_parts.append(text)
                    logger.debug(f"Found context part: {text[:100]}...")

        # Kết hợp các phần thành câu trả lời và ngữ cảnh hoàn chỉnh
        qa_data['answer'] = ' '.join(answer_parts)
        qa_data['context'] = ' '.join(context_parts)
        
        return qa_data

    def parse(self, response):
        try:
            logger.info(f"Parsing URL: {response.url}")
            
            # Lấy tiêu đề chính
            title = response.xpath('//h1/text()').get()
            if not title:
                title = response.xpath('/html/body/div[6]/div/div[1]/article/div[1]/div/header/h1/text()').get()
            title = self.clean_text(title)
            logger.info(f"Found title: {title}")

            # Lấy tất cả thẻ h2 làm câu hỏi
            questions = response.xpath('//*[@id="news-content"]/h2')
            logger.info(f"Found {len(questions)} potential questions")
            
            qa_pairs = []
            
            # Tạo ID duy nhất cho mỗi cặp Q&A
            base_id = datetime.now().strftime("%Y%m%d")
            
            for idx, question in enumerate(questions, 1):
                logger.info(f"Processing question {idx}/{len(questions)}")
                qa_data = self.extract_qa_context(question)
                
                # Chỉ thêm vào kết quả nếu có đủ câu hỏi và câu trả lời
                if qa_data['question'] and qa_data['answer']:
                    qa_item = {
                        'id': f"{base_id}_{idx}",
                        'url': response.url,
                        'title': title,
                        'question': qa_data['question'],
                        'answer': qa_data['answer'],
                        'context': qa_data['context'] if qa_data['context'] else None,
                        'source': 'thuvienphapluat.vn',
                        'crawled_at': datetime.now().isoformat()
                    }
                    qa_pairs.append(qa_item)
                    logger.info(f"Added QA pair {idx} with id {qa_item['id']}")
                else:
                    logger.warning(f"Skipped question {idx} due to missing question or answer")

            # Trả về danh sách các cặp Q&A
            for qa_pair in qa_pairs:
                yield qa_pair
                
            logger.info(f"Successfully crawled {len(qa_pairs)} QA pairs from: {response.url}")
            
        except Exception as e:
            logger.error(f"Error parsing {response.url}: {str(e)}", exc_info=True)

def main():
    # Lấy đường dẫn tuyệt đối cho output file
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_file = os.path.join(root_dir, 'data', 'json', 'legal_qa_output_v2.json')
    
    logger.info(f"Output will be saved to: {output_file}")
    
    # Cấu hình crawler
    process = CrawlerProcess(settings={
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 16,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 8,
        'DOWNLOAD_DELAY': 1,
        'COOKIES_ENABLED': False,
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 522, 524, 408, 429],
        'FEED_FORMAT': 'json',
        'FEED_URI': output_file,
        'FEED_EXPORT_ENCODING': 'utf-8',
        'FEED_EXPORT_INDENT': 2,
        'LOG_LEVEL': 'INFO'
    })

    # Chạy spider
    process.crawl(LegalQACrawlerV2)
    process.start()

if __name__ == '__main__':
    main() 