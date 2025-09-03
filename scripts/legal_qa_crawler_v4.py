import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.http import Response
from scrapy.selector import Selector
import json
import logging
import os
import re
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ElementType(Enum):
    """Enum for HTML element types."""
    PARAGRAPH = 'p'
    BLOCKQUOTE = 'blockquote'
    TABLE = 'table'
    HEADING = 'h2'


@dataclass
class QAPair:
    """Data class for Question-Answer pair."""
    question: str
    answers: List[Dict[str, Any]]


@dataclass
class ArticleData:
    """Data class for article data."""
    id: str
    url: str
    title: str
    source: str
    crawled_at: str
    qa_pairs: List[QAPair]


class CrawlerConfig:
    """Configuration constants for the crawler."""
    
    # XPath selectors
    TITLE_SELECTORS = [
        '//h1/text()',
        '/html/body/div[6]/div/div[1]/article/div[1]/div/header/h1/text()'
    ]
    
    QUESTIONS_SELECTOR = '//*[@id="news-content"]/h2'
    
    # Default values
    DEFAULT_SOURCE = 'thuvienphapluat.vn'
    DEFAULT_SLUG = 'default'
    
    # Text processing
    MIN_QUESTION_LENGTH = 10
    MIN_ANSWER_LENGTH = 20


class TextProcessor:
    """Utility class for text processing operations."""
    
    @staticmethod
    def clean_text(text: Optional[str]) -> Optional[str]:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text or None if empty
        """
        if not text:
            return None
        
        # Remove extra whitespace but preserve structure
        lines = text.split('\n')
        cleaned_lines = [' '.join(line.split()) for line in lines if line.strip()]
        return ' '.join(cleaned_lines)
    
    @staticmethod
    def is_valid_question(text: str) -> bool:
        """Check if text is a valid question."""
        return len(text) >= CrawlerConfig.MIN_QUESTION_LENGTH
    
    @staticmethod
    def is_valid_answer(text: str) -> bool:
        """Check if text is a valid answer."""
        return len(text) >= CrawlerConfig.MIN_ANSWER_LENGTH


class TableConverter:
    """Utility class for converting HTML tables to markdown."""
    
    @staticmethod
    def to_markdown(table_element: Selector) -> str:
        """
        Convert HTML table to markdown format.
        
        Args:
            table_element: Scrapy selector for table element
            
        Returns:
            Markdown formatted table string
        """
        try:
            rows = table_element.xpath('.//tr')
            if not rows:
                return ""

            markdown_rows = []
            
            # Process header row
            header_cells = rows[0].xpath('.//th|.//td')
            if header_cells:
                headers = [
                    TextProcessor.clean_text(cell.xpath('string()').get()) or '' 
                    for cell in header_cells
                ]
                markdown_rows.append('| ' + ' | '.join(headers) + ' |')
                markdown_rows.append('|' + '|'.join(['---' for _ in headers]) + '|')
            
            # Process data rows
            for row in rows[1:]:
                cells = row.xpath('.//td')
                if cells:
                    cell_data = [
                        TextProcessor.clean_text(cell.xpath('string()').get()) or '' 
                        for cell in cells
                    ]
                    markdown_rows.append('| ' + ' | '.join(cell_data) + ' |')
            
            return '\n'.join(markdown_rows)
            
        except Exception as e:
            logger.error(f"Error converting table to markdown: {str(e)}")
            return ""


class QAPairExtractor:
    """Class responsible for extracting Q&A pairs from HTML elements."""
    
    def __init__(self):
        self.text_processor = TextProcessor()
        self.table_converter = TableConverter()
    
    def extract_qa_pairs(self, question_element: Selector) -> QAPair:
        """
        Extract question and answer pairs from a question element.
        
        Args:
            question_element: Scrapy selector for question element
            
        Returns:
            QAPair object with question and answers
        """
        qa_data = QAPair(question='', answers=[])
        
        try:
            # Extract question text
            question_text = self._extract_question_text(question_element)
            if not question_text:
                logger.warning("Empty question text found")
                return qa_data
            
            qa_data.question = question_text
            logger.debug(f"Extracted question: {question_text}")
            
            # Extract answers and contexts
            qa_data.answers = self._extract_answers_and_contexts(question_element)
            
            # Validate results
            if not qa_data.answers:
                logger.warning(f"No valid answers found for question: {question_text[:100]}")
            else:
                logger.info(f"Successfully extracted {len(qa_data.answers)} answers")
                
        except Exception as e:
            logger.error(f"Error extracting QA pairs: {str(e)}", exc_info=True)
            
        return qa_data
    
    def _extract_question_text(self, question_element: Selector) -> Optional[str]:
        """Extract and validate question text."""
        question_text = self.text_processor.clean_text(
            question_element.xpath('string()').get()
        )
        
        if question_text and self.text_processor.is_valid_question(question_text):
            return question_text
        return None
    
    def _extract_answers_and_contexts(self, question_element: Selector) -> List[Dict[str, Any]]:
        """Extract answers and their contexts from following elements."""
        next_elements = question_element.xpath('following-sibling::*')
        answers = []
        
        current_answer = None
        current_contexts = []
        
        for element in next_elements:
            element_type = element.xpath('name()').get()
            
            # Stop at next heading
            if element_type == ElementType.HEADING.value:
                self._save_current_answer(answers, current_answer, current_contexts)
                break
            
            # Process different element types
            if element_type == ElementType.PARAGRAPH.value:
                current_answer, current_contexts = self._process_paragraph(
                    element, answers, current_answer, current_contexts
                )
            elif element_type == ElementType.BLOCKQUOTE.value:
                current_contexts = self._process_blockquote(element, current_answer, current_contexts)
            elif element_type == ElementType.TABLE.value:
                current_contexts = self._process_table(element, current_answer, current_contexts)
        
        # Save final answer
        self._save_current_answer(answers, current_answer, current_contexts)
        
        # Filter valid answers
        return [ans for ans in answers if ans.get('answer')]
    
    def _process_paragraph(self, element: Selector, answers: List[Dict], 
                          current_answer: Optional[str], 
                          current_contexts: List[str]) -> Tuple[Optional[str], List[str]]:
        """Process paragraph element as potential answer."""
        text = self.text_processor.clean_text(element.xpath('string()').get())
        
        if text and self.text_processor.is_valid_answer(text):
            # Save previous answer if exists
            if current_answer:
                self._save_current_answer(answers, current_answer, current_contexts)
            
            # Start new answer
            current_answer = text
            current_contexts = []
            logger.debug(f"Found new answer: {text[:100]}")
        
        return current_answer, current_contexts
    
    def _process_blockquote(self, element: Selector, current_answer: Optional[str], 
                           current_contexts: List[str]) -> List[str]:
        """Process blockquote element as context."""
        if not current_answer:
            return current_contexts
        
        text = self.text_processor.clean_text(element.xpath('string()').get())
        if text:
            current_contexts.append(text)
            logger.debug(f"Added blockquote context: {text[:100]}")
        
        return current_contexts
    
    def _process_table(self, element: Selector, current_answer: Optional[str], 
                      current_contexts: List[str]) -> List[str]:
        """Process table element as context."""
        if not current_answer:
            return current_contexts
        
        markdown_table = self.table_converter.to_markdown(element)
        if markdown_table:
            current_contexts.append(markdown_table)
            logger.debug(f"Added table context: {markdown_table[:100]}")
        
        return current_contexts
    
    def _save_current_answer(self, answers: List[Dict], current_answer: Optional[str], 
                           current_contexts: List[str]) -> None:
        """Save current answer and contexts to answers list."""
        if current_answer:
            answers.append({
                'answer': current_answer,
                'contexts': current_contexts
            })


class LegalQACrawlerV4(scrapy.Spider):
    """Optimized legal QA crawler with improved structure and performance."""
    
    name = 'legal_qa_v4'
    
    def __init__(self, urls_file: Optional[str] = None, *args, **kwargs):
        super(LegalQACrawlerV4, self).__init__(*args, **kwargs)
        
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.slug = self._extract_slug_from_urls_file(urls_file)
        self.qa_extractor = QAPairExtractor()
        
        logger.info(f"Using slug: {self.slug}")
        self.start_urls = self._load_urls_from_file(urls_file)
    
    def _extract_slug_from_urls_file(self, urls_file: Optional[str]) -> str:
        """Extract slug from URLs file name."""
        if not urls_file:
            return CrawlerConfig.DEFAULT_SLUG
        
        try:
            filename = os.path.basename(urls_file)
            filename = os.path.splitext(filename)[0]
            parts = filename.split('_')
            
            if len(parts) >= 3 and parts[0] == 'legal' and parts[1] == 'qa' and parts[-1] == 'urls':
                return '_'.join(parts[2:-1])
            return CrawlerConfig.DEFAULT_SLUG
        except Exception as e:
            logger.error(f"Error extracting slug from filename: {str(e)}")
            return CrawlerConfig.DEFAULT_SLUG
    
    def _load_urls_from_file(self, urls_file: Optional[str]) -> List[str]:
        """Load URLs from JSON file."""
        if not urls_file:
            logger.warning("No URLs file provided")
            return []
        
        try:
            logger.info(f"Reading URLs from: {urls_file}")
            with open(urls_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                urls = [item['url'] for item in data]
                logger.info(f"Loaded {len(urls)} URLs to crawl")
                return urls
        except Exception as e:
            logger.error(f"Error loading URLs: {str(e)}")
            return []
    
    def _extract_title(self, response: Response) -> str:
        """Extract article title from response."""
        for selector in CrawlerConfig.TITLE_SELECTORS:
            title = response.xpath(selector).get()
            if title:
                return TextProcessor.clean_text(title) or "Unknown Title"
        return "Unknown Title"
    
    def _extract_questions(self, response: Response) -> List[Selector]:
        """Extract question elements from response."""
        questions = response.xpath(CrawlerConfig.QUESTIONS_SELECTOR)
        logger.info(f"Found {len(questions)} potential questions")
        return questions
    
    def _create_article_data(self, response: Response, qa_pairs: List[QAPair]) -> ArticleData:
        """Create ArticleData object from response and QA pairs."""
        article_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return ArticleData(
            id=article_id,
            url=response.url,
            title=self._extract_title(response),
            source=CrawlerConfig.DEFAULT_SOURCE,
            crawled_at=datetime.now().isoformat(),
            qa_pairs=qa_pairs
        )
    
    def parse(self, response: Response) -> Optional[ArticleData]:
        """
        Parse response and extract QA pairs.
        
        Args:
            response: Scrapy response object
            
        Yields:
            ArticleData object if valid QA pairs found
        """
        try:
            logger.info(f"Parsing URL: {response.url}")
            
            # Extract questions
            questions = self._extract_questions(response)
            if not questions:
                logger.warning(f"No questions found in {response.url}")
                return
            
            # Process each question
            qa_pairs = []
            for idx, question in enumerate(questions, 1):
                logger.info(f"Processing question {idx}/{len(questions)}")
                qa_data = self.qa_extractor.extract_qa_pairs(question)
                
                # Only add valid QA pairs
                if qa_data.question and qa_data.answers:
                    qa_pairs.append(qa_data)
                    logger.info(f"Added question {idx} with {len(qa_data.answers)} answers")
                else:
                    logger.warning(f"Skipped question {idx} due to missing question or answers")
            
            # Yield article data if valid QA pairs found
            if qa_pairs:
                article_data = self._create_article_data(response, qa_pairs)
                logger.info(f"Successfully processed article with {len(qa_pairs)} QA pairs")
                yield asdict(article_data)
            
        except Exception as e:
            logger.error(f"Error parsing {response.url}: {str(e)}", exc_info=True)


def create_crawler_process(urls_file: str, output_file: str) -> CrawlerProcess:
    """Create and configure crawler process."""
    
    settings = {
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
    }
    
    process = CrawlerProcess(settings=settings)
    process.crawl(LegalQACrawlerV4, urls_file=urls_file)
    
    return process


def main():
    """Main function to run the crawler."""
    # Get absolute paths
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    urls_file = os.path.join(root_dir, 'data', 'json', 'legal_qa_thue-phi-le-phi_urls.json')
    
    # Create crawler instance to get slug
    crawler = LegalQACrawlerV4(urls_file=urls_file)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(root_dir, 'data', 'json', f'legal_qa_{crawler.slug}_{timestamp}.json')
    
    logger.info(f"Output will be saved to: {output_file}")
    
    # Create and run crawler process
    process = create_crawler_process(urls_file, output_file)
    process.start()


if __name__ == '__main__':
    main()
