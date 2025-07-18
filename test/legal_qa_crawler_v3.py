import scrapy
from scrapy.crawler import CrawlerProcess
import json
import logging
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def extract_slug_from_urls_file(urls_file: str) -> str:
    """Extract slug from urls file name.
    Example: 'legal_qa_giao-thong-van-tai_urls.json' -> 'giao-thong-van-tai'
    """
    try:
        # Get filename without path and extension
        filename = os.path.basename(urls_file)
        # Remove extension
        filename = os.path.splitext(filename)[0]
        # Split by underscore and get the relevant part
        parts = filename.split('_')
        # The slug should be between 'legal_qa' and 'urls'
        if len(parts) >= 3 and parts[0] == 'legal' and parts[1] == 'qa' and parts[-1] == 'urls':
            return '_'.join(parts[2:-1])
        return 'default'
    except Exception as e:
        logger.error(f"Error extracting slug from filename: {str(e)}")
        return 'default'

class LegalQACrawlerV3(scrapy.Spider):
    name = 'legal_qa_v3'
    
    def __init__(self, urls_file=None, *args, **kwargs):
        super(LegalQACrawlerV3, self).__init__(*args, **kwargs)
        # Lấy đường dẫn tuyệt đối của thư mục gốc
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Nếu không có urls_file được cung cấp, sử dụng đường dẫn mặc định
        if not urls_file:
            urls_file = os.path.join(self.root_dir, 'data', 'json', 'legal_qa_giao-thong-van-tai_urls.json')
        
        # Extract slug from urls file
        self.slug = extract_slug_from_urls_file(urls_file)
        logger.info(f"Using slug: {self.slug}")
        
        # Đọc URLs từ file JSON
        try:
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

    def table_to_markdown(self, table_element) -> str:
        """Chuyển đổi HTML table sang định dạng markdown.
        
        Args:
            table_element: Phần tử table từ response.
            
        Returns:
            str: Bảng ở định dạng markdown.
        """
        try:
            # Lấy tất cả các hàng
            rows = table_element.xpath('.//tr')
            if not rows:
                return ""

            # Khởi tạo danh sách để lưu các hàng markdown
            markdown_rows = []
            
            # Xử lý header (hàng đầu tiên)
            header_cells = rows[0].xpath('.//th|.//td')
            if header_cells:
                # Lấy text từ các ô header và làm sạch
                headers = [self.clean_text(cell.xpath('string()').get()) or '' for cell in header_cells]
                # Thêm hàng header
                markdown_rows.append('| ' + ' | '.join(headers) + ' |')
                # Thêm dòng phân cách
                markdown_rows.append('|' + '|'.join(['---' for _ in headers]) + '|')
            
            # Xử lý các hàng dữ liệu
            for row in rows[1:]:
                cells = row.xpath('.//td')
                if cells:
                    # Lấy text từ các ô và làm sạch
                    cell_data = [self.clean_text(cell.xpath('string()').get()) or '' for cell in cells]
                    # Thêm hàng dữ liệu
                    markdown_rows.append('| ' + ' | '.join(cell_data) + ' |')
            
            # Kết hợp tất cả các hàng thành một chuỗi markdown
            return '\n'.join(markdown_rows)
            
        except Exception as e:
            logger.error(f"Error converting table to markdown: {str(e)}")
            return ""

    def extract_qa_pairs(self, question_element) -> Dict:
        """Trích xuất câu hỏi và các cặp câu trả lời - ngữ cảnh từ một phần tử h2"""
        # Khởi tạo cấu trúc dữ liệu
        qa_data = {
            'question': '',
            'answers': []  # List các câu trả lời và ngữ cảnh tương ứng
        }
        
        try:
            # Lấy nội dung câu hỏi
            question_text = self.clean_text(question_element.xpath('string()').get())
            if not question_text:
                logger.warning("Empty question text found")
                return qa_data
                
            qa_data['question'] = question_text
            logger.debug(f"Extracted question: {question_text}")
            
            # Lấy tất cả các phần tử sau h2 cho đến h2 tiếp theo
            next_elements = question_element.xpath('following-sibling::*')
            
            current_answer = None
            current_contexts = []
            
            for element in next_elements:
                element_type = element.xpath('name()').get()
                
                # Dừng nếu gặp h2 tiếp theo
                if element_type == 'h2':
                    # Lưu cặp answer-contexts cuối cùng nếu có
                    if current_answer:
                        qa_data['answers'].append({
                            'answer': current_answer,
                            'contexts': current_contexts
                        })
                    break
                
                # Xử lý phần tử p là câu trả lời
                if element_type == 'p':
                    text = self.clean_text(element.xpath('string()').get())
                    if text:
                        # Nếu đã có answer trước đó, lưu cặp answer-contexts cũ
                        if current_answer:
                            qa_data['answers'].append({
                                'answer': current_answer,
                                'contexts': current_contexts
                            })
                        
                        # Bắt đầu answer mới với contexts rỗng
                        current_answer = text
                        current_contexts = []
                        logger.debug(f"Found new answer: {text[:100] if text else ''}")
                
                # Xử lý phần tử blockquote là ngữ cảnh
                elif element_type == 'blockquote':
                    text = self.clean_text(element.xpath('string()').get())
                    if text and current_answer:  # Chỉ thêm context nếu đã có answer
                        current_contexts.append(text)
                        logger.debug(f"Added blockquote context to current answer: {text[:100] if text else ''}")
                
                # Xử lý phần tử table là ngữ cảnh
                elif element_type == 'table':
                    markdown_table = self.table_to_markdown(element)
                    if markdown_table and current_answer:  # Chỉ thêm context nếu đã có answer và bảng không rỗng
                        current_contexts.append(markdown_table)
                        logger.debug(f"Added table context to current answer: {markdown_table[:100] if markdown_table else ''}")
            
            # Thêm cặp answer-contexts cuối cùng nếu có
            if current_answer:
                qa_data['answers'].append({
                    'answer': current_answer,
                    'contexts': current_contexts
                })
            
            # Lọc ra các cặp có answer không rỗng
            qa_data['answers'] = [ans for ans in qa_data['answers'] if ans.get('answer')]
            
            if not qa_data['answers']:
                logger.warning(f"No valid answers found for question: {question_text[:100]}")
            else:
                logger.info(f"Successfully extracted {len(qa_data['answers'])} answers with their contexts")
                
        except Exception as e:
            logger.error(f"Error extracting QA pairs: {str(e)}", exc_info=True)
            
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
            
            # Tạo ID duy nhất cho bài viết
            article_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Xử lý từng câu hỏi
            qa_pairs = []
            for idx, question in enumerate(questions, 1):
                logger.info(f"Processing question {idx}/{len(questions)}")
                qa_data = self.extract_qa_pairs(question)
                
                # Chỉ thêm vào kết quả nếu có câu hỏi và ít nhất một câu trả lời
                if qa_data['question'] and qa_data['answers']:
                    qa_pairs.append(qa_data)
                    logger.info(f"Added question {idx} with {len(qa_data['answers'])} answers")
                else:
                    logger.warning(f"Skipped question {idx} due to missing question or answers")

            # Nếu có ít nhất một cặp Q&A hợp lệ
            if qa_pairs:
                article_data = {
                    'id': article_id,
                    'url': response.url,
                    'title': title,
                    'source': 'thuvienphapluat.vn',
                    'crawled_at': datetime.now().isoformat(),
                    'qa_pairs': qa_pairs
                }
                yield article_data
                logger.info(f"Successfully processed article with {len(qa_pairs)} QA pairs")
            
        except Exception as e:
            logger.error(f"Error parsing {response.url}: {str(e)}", exc_info=True)

def main():
    # Lấy đường dẫn tuyệt đối cho output file
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Cho phép chỉ định urls_file qua command line
    import sys
    urls_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Khởi tạo crawler với urls_file (có thể là None)
    crawler = LegalQACrawlerV3(urls_file=urls_file)
    
    # Sử dụng slug từ crawler để tạo output file
    output_file = os.path.join(root_dir, 'data', 'json', f'legal_qa_{crawler.slug}_output.json')
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
    process.crawl(LegalQACrawlerV3, urls_file=urls_file)
    process.start()

if __name__ == '__main__':
    main() 