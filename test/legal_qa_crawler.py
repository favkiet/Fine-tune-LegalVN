import scrapy
from scrapy.crawler import CrawlerProcess
import json
from concurrent.futures import ThreadPoolExecutor
import logging

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LegalQACrawler(scrapy.Spider):
    name = 'legal_qa'
    
    def __init__(self, *args, **kwargs):
        super(LegalQACrawler, self).__init__(*args, **kwargs)
        # Đọc URLs từ file JSON
        try:
            with open('data/json/legal_qa_urls.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.start_urls = [item['url'] for item in data]
                logger.info(f"Loaded {len(self.start_urls)} URLs to crawl")
        except Exception as e:
            logger.error(f"Error loading URLs: {str(e)}")
            self.start_urls = []

    def clean_text(self, text):
        if not text:
            return None
        # Clean whitespace while preserving structure
        return ' '.join(text.split())

    def parse(self, response):
        try:
            # Extract main title
            title = response.xpath('/html/body/div[6]/div/div[1]/article/div[1]/div/header/h1/text()').get()
            title = self.clean_text(title)

            # Get all h2 headers as questions
            questions = response.xpath('//*[@id="news-content"]/h2')
            qa_pairs = []

            for question in questions:
                question_text = self.clean_text(question.xpath('string()').get())
                
                # Get all elements after this h2 until the next h2 or end
                answer_elements = []
                current_element = question.xpath('following-sibling::*')
                
                for element in current_element:
                    # Stop if we hit another h2
                    if element.xpath('name()').get() == 'h2':
                        break
                    
                    # Get text from paragraphs and blockquotes
                    if element.xpath('name()').get() in ['p', 'blockquote']:
                        text = self.clean_text(element.xpath('string()').get())
                        if text:
                            answer_elements.append(text)

                if question_text and answer_elements:
                    qa_pairs.append({
                        'question': question_text,
                        'answers': answer_elements
                    })

            yield {
                'url': response.url,
                'title': title,
                'qa_pairs': qa_pairs
            }
            logger.info(f"Successfully crawled: {response.url}")
            
        except Exception as e:
            logger.error(f"Error parsing {response.url}: {str(e)}")

def main():
    # Configure crawler settings
    process = CrawlerProcess(settings={
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 16,  # Số request đồng thời
        'CONCURRENT_REQUESTS_PER_DOMAIN': 8,  # Số request đồng thời trên mỗi domain
        'DOWNLOAD_DELAY': 1,  # Delay giữa các request (giây)
        'COOKIES_ENABLED': False,  # Tắt cookies để tăng tốc
        'RETRY_ENABLED': True,  # Cho phép thử lại khi fail
        'RETRY_TIMES': 3,  # Số lần thử lại
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 522, 524, 408, 429],  # Mã lỗi cần thử lại
        'FEED_FORMAT': 'json',
        'FEED_URI': 'data/json/qa-tien-te-ngan-hang.json',
        'FEED_EXPORT_ENCODING': 'utf-8',
        'FEED_EXPORT_INDENT': 2,
        'LOG_LEVEL': 'INFO'
    })

    # Run the spider
    process.crawl(LegalQACrawler)
    process.start()

if __name__ == '__main__':
    main()
    
    
