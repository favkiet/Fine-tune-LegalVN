"""
Unit tests for legal_qa_crawler.py

This module contains comprehensive unit tests for the legal QA crawler functionality
including text processing, QA extraction, HTML parsing, and crawler operations.
"""

import unittest
from unittest.mock import Mock, patch, mock_open, MagicMock
import json
import sys
from pathlib import Path
from datetime import datetime

# Add the scripts directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from legal_qa_crawler import (
    ElementType,
    QAPair,
    ArticleData,
    CrawlerConfig,
    TextProcessor,
    TableConverter,
    QAPairExtractor,
    LegalQACrawlerV4,
    create_crawler_process,
    main
)


class TestDataClasses(unittest.TestCase):
    """Test cases for data classes."""

    def test_qa_pair_creation(self):
        """Test QAPair creation."""
        answers = [{'answer': 'Test answer', 'contexts': ['Test context']}]
        qa_pair = QAPair(question='Test question?', answers=answers)
        
        self.assertEqual(qa_pair.question, 'Test question?')
        self.assertEqual(qa_pair.answers, answers)

    def test_article_data_creation(self):
        """Test ArticleData creation."""
        qa_pairs = [QAPair(question='Test?', answers=[])]
        article = ArticleData(
            id='art-123',
            url='https://example.com/article',
            title='Test Article',
            source='test.com',
            crawled_at='2023-01-01T00:00:00',
            qa_pairs=qa_pairs
        )
        
        self.assertEqual(article.id, 'art-123')
        self.assertEqual(article.url, 'https://example.com/article')
        self.assertEqual(article.title, 'Test Article')
        self.assertEqual(article.source, 'test.com')
        self.assertEqual(article.crawled_at, '2023-01-01T00:00:00')
        self.assertEqual(article.qa_pairs, qa_pairs)


class TestElementType(unittest.TestCase):
    """Test cases for ElementType enum."""

    def test_element_types(self):
        """Test element type values."""
        self.assertEqual(ElementType.PARAGRAPH.value, 'p')
        self.assertEqual(ElementType.BLOCKQUOTE.value, 'blockquote')
        self.assertEqual(ElementType.TABLE.value, 'table')
        self.assertEqual(ElementType.HEADING.value, 'h2')


class TestTextProcessor(unittest.TestCase):
    """Test cases for TextProcessor class."""

    def test_clean_text_normal(self):
        """Test cleaning normal text."""
        text = "  This is a\n  test   text  with\nextra    spaces  "
        expected = "This is a test text with extra spaces"
        result = TextProcessor.clean_text(text)
        self.assertEqual(result, expected)

    def test_clean_text_multiline_with_structure(self):
        """Test cleaning text with multiple lines."""
        text = "Line 1\n\nLine 2\n   Line 3   \n"
        expected = "Line 1 Line 2 Line 3"
        result = TextProcessor.clean_text(text)
        self.assertEqual(result, expected)

    def test_clean_text_empty(self):
        """Test cleaning empty text."""
        result = TextProcessor.clean_text("")
        self.assertIsNone(result)

    def test_clean_text_none(self):
        """Test cleaning None text."""
        result = TextProcessor.clean_text(None)
        self.assertIsNone(result)

    def test_clean_text_whitespace_only(self):
        """Test cleaning whitespace-only text."""
        text = "   \n  \t  \n  "
        result = TextProcessor.clean_text(text)
        self.assertEqual(result, "")

    def test_is_valid_question_valid(self):
        """Test valid question validation."""
        question = "This is a valid question that meets minimum length requirement?"
        self.assertTrue(TextProcessor.is_valid_question(question))

    def test_is_valid_question_too_short(self):
        """Test invalid question validation."""
        question = "Short?"
        self.assertFalse(TextProcessor.is_valid_question(question))

    def test_is_valid_answer_valid(self):
        """Test valid answer validation."""
        answer = "This is a valid answer that meets the minimum length requirement for answers."
        self.assertTrue(TextProcessor.is_valid_answer(answer))

    def test_is_valid_answer_too_short(self):
        """Test invalid answer validation."""
        answer = "Short answer."
        self.assertFalse(TextProcessor.is_valid_answer(answer))


class TestTableConverter(unittest.TestCase):
    """Test cases for TableConverter class."""

    def setUp(self):
        """Set up test fixtures."""
        self.converter = TableConverter()

    def test_to_markdown_simple_table(self):
        """Test conversion of simple table to markdown."""
        # Mock table element
        mock_table = Mock()
        
        # Mock header row
        mock_header_row = Mock()
        mock_header_cell1 = Mock()
        mock_header_cell1.xpath.return_value.get.return_value = "Header 1"
        mock_header_cell2 = Mock()
        mock_header_cell2.xpath.return_value.get.return_value = "Header 2"
        mock_header_row.xpath.return_value = [mock_header_cell1, mock_header_cell2]
        
        # Mock data row
        mock_data_row = Mock()
        mock_data_cell1 = Mock()
        mock_data_cell1.xpath.return_value.get.return_value = "Data 1"
        mock_data_cell2 = Mock()
        mock_data_cell2.xpath.return_value.get.return_value = "Data 2"
        mock_data_row.xpath.return_value = [mock_data_cell1, mock_data_cell2]
        
        mock_table.xpath.return_value = [mock_header_row, mock_data_row]
        
        result = self.converter.to_markdown(mock_table)
        
        expected_lines = [
            "| Header 1 | Header 2 |",
            "|---|---|",
            "| Data 1 | Data 2 |"
        ]
        expected = "\n".join(expected_lines)
        
        self.assertEqual(result, expected)

    def test_to_markdown_empty_table(self):
        """Test conversion of empty table."""
        mock_table = Mock()
        mock_table.xpath.return_value = []
        
        result = self.converter.to_markdown(mock_table)
        
        self.assertEqual(result, "")

    def test_to_markdown_error_handling(self):
        """Test table conversion error handling."""
        mock_table = Mock()
        mock_table.xpath.side_effect = Exception("XPath error")
        
        result = self.converter.to_markdown(mock_table)
        
        self.assertEqual(result, "")


class TestQAPairExtractor(unittest.TestCase):
    """Test cases for QAPairExtractor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.extractor = QAPairExtractor()

    def test_extract_question_text_valid(self):
        """Test extraction of valid question text."""
        mock_element = Mock()
        mock_element.xpath.return_value.get.return_value = "This is a valid question that is long enough?"
        
        result = self.extractor._extract_question_text(mock_element)
        
        self.assertEqual(result, "This is a valid question that is long enough?")

    def test_extract_question_text_too_short(self):
        """Test extraction of invalid (too short) question text."""
        mock_element = Mock()
        mock_element.xpath.return_value.get.return_value = "Hi?"
        
        result = self.extractor._extract_question_text(mock_element)
        
        self.assertIsNone(result)

    def test_extract_question_text_empty(self):
        """Test extraction of empty question text."""
        mock_element = Mock()
        mock_element.xpath.return_value.get.return_value = None
        
        result = self.extractor._extract_question_text(mock_element)
        
        self.assertIsNone(result)

    def test_process_paragraph_as_answer(self):
        """Test processing paragraph as answer."""
        mock_element = Mock()
        mock_element.xpath.return_value.get.return_value = "This is a valid answer that is long enough to pass validation."
        
        current_answer, current_contexts = self.extractor._process_paragraph(
            mock_element, [], None, []
        )
        
        self.assertEqual(current_answer, "This is a valid answer that is long enough to pass validation.")
        self.assertEqual(current_contexts, [])

    def test_process_paragraph_saves_previous_answer(self):
        """Test that processing new paragraph saves previous answer."""
        answers = []
        mock_element = Mock()
        mock_element.xpath.return_value.get.return_value = "This is a new valid answer that is long enough to pass validation."
        
        current_answer, current_contexts = self.extractor._process_paragraph(
            mock_element, answers, "Previous answer that was long enough", ["Previous context"]
        )
        
        # Should save previous answer
        self.assertEqual(len(answers), 1)
        self.assertEqual(answers[0]['answer'], "Previous answer that was long enough")
        self.assertEqual(answers[0]['contexts'], ["Previous context"])
        
        # Should set new answer
        self.assertEqual(current_answer, "This is a new valid answer that is long enough to pass validation.")
        self.assertEqual(current_contexts, [])

    def test_process_blockquote_as_context(self):
        """Test processing blockquote as context."""
        mock_element = Mock()
        mock_element.xpath.return_value.get.return_value = "This is context content."
        
        current_contexts = self.extractor._process_blockquote(
            mock_element, "Current answer", ["Existing context"]
        )
        
        expected = ["Existing context", "This is context content."]
        self.assertEqual(current_contexts, expected)

    def test_process_blockquote_no_current_answer(self):
        """Test processing blockquote when no current answer exists."""
        mock_element = Mock()
        mock_element.xpath.return_value.get.return_value = "This is context content."
        
        current_contexts = self.extractor._process_blockquote(
            mock_element, None, ["Existing context"]
        )
        
        # Should return unchanged contexts
        self.assertEqual(current_contexts, ["Existing context"])

    @patch('legal_qa_crawler.TableConverter.to_markdown')
    def test_process_table_as_context(self, mock_to_markdown):
        """Test processing table as context."""
        mock_element = Mock()
        mock_to_markdown.return_value = "| Header | Data |\n|---|---|\n| Cell1 | Cell2 |"
        
        current_contexts = self.extractor._process_table(
            mock_element, "Current answer", ["Existing context"]
        )
        
        expected = ["Existing context", "| Header | Data |\n|---|---|\n| Cell1 | Cell2 |"]
        self.assertEqual(current_contexts, expected)

    def test_save_current_answer(self):
        """Test saving current answer and contexts."""
        answers = []
        
        self.extractor._save_current_answer(
            answers, "Test answer content", ["Context 1", "Context 2"]
        )
        
        self.assertEqual(len(answers), 1)
        self.assertEqual(answers[0]['answer'], "Test answer content")
        self.assertEqual(answers[0]['contexts'], ["Context 1", "Context 2"])

    def test_save_current_answer_no_answer(self):
        """Test saving when no current answer exists."""
        answers = []
        
        self.extractor._save_current_answer(answers, None, ["Context 1"])
        
        self.assertEqual(len(answers), 0)

    def test_extract_qa_pairs_complete_flow(self):
        """Test complete QA pair extraction flow."""
        # Mock question element
        mock_question_element = Mock()
        
        # Mock the xpath calls for question text
        mock_question_element.xpath.side_effect = [
            Mock(get=Mock(return_value="This is a valid test question that is long enough?")),  # Question text
            []  # No following elements - we'll mock the actual extraction method
        ]
        
        # Mock the _extract_answers_and_contexts method to return expected result
        with patch.object(self.extractor, '_extract_answers_and_contexts') as mock_extract:
            mock_extract.return_value = [
                {
                    'answer': 'This is a valid answer that is long enough to pass validation.',
                    'contexts': ['This is context content.']
                }
            ]
            
            result = self.extractor.extract_qa_pairs(mock_question_element)
        
        self.assertEqual(result.question, "This is a valid test question that is long enough?")
        self.assertEqual(len(result.answers), 1)
        self.assertEqual(result.answers[0]['answer'], "This is a valid answer that is long enough to pass validation.")
        self.assertEqual(result.answers[0]['contexts'], ["This is context content."])


class TestLegalQACrawlerV4(unittest.TestCase):
    """Test cases for LegalQACrawlerV4 class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_urls_data = [
            {"url": "https://example.com/article1", "title": "Article 1"},
            {"url": "https://example.com/article2", "title": "Article 2"}
        ]

    def test_extract_slug_from_urls_file(self):
        """Test slug extraction from URLs file."""
        crawler = LegalQACrawlerV4()
        
        # Test valid filename
        result = crawler._extract_slug_from_urls_file('legal_qa_thue-phi-le-phi_urls.json')
        self.assertEqual(result, 'thue-phi-le-phi')
        
        # Test invalid filename
        result = crawler._extract_slug_from_urls_file('invalid_filename.json')
        self.assertEqual(result, CrawlerConfig.DEFAULT_SLUG)
        
        # Test None input
        result = crawler._extract_slug_from_urls_file(None)
        self.assertEqual(result, CrawlerConfig.DEFAULT_SLUG)

    @patch('builtins.open', new_callable=mock_open)
    @patch('legal_qa_crawler.json.load')
    def test_load_urls_from_file_success(self, mock_json_load, mock_file):
        """Test successful URL loading from file."""
        mock_json_load.return_value = self.test_urls_data
        
        crawler = LegalQACrawlerV4()
        result = crawler._load_urls_from_file('test_urls.json')
        
        expected = ["https://example.com/article1", "https://example.com/article2"]
        self.assertEqual(result, expected)
        mock_file.assert_called_once_with('test_urls.json', 'r', encoding='utf-8')

    def test_load_urls_from_file_none(self):
        """Test URL loading with None file."""
        crawler = LegalQACrawlerV4()
        result = crawler._load_urls_from_file(None)
        
        self.assertEqual(result, [])

    @patch('builtins.open')
    def test_load_urls_from_file_error(self, mock_file):
        """Test URL loading with file error."""
        mock_file.side_effect = FileNotFoundError("File not found")
        
        crawler = LegalQACrawlerV4()
        result = crawler._load_urls_from_file('nonexistent.json')
        
        self.assertEqual(result, [])

    def test_extract_title_success(self):
        """Test successful title extraction."""
        crawler = LegalQACrawlerV4()
        mock_response = Mock()
        mock_response.xpath.side_effect = [
            Mock(get=Mock(return_value="Test Article Title"))  # First selector succeeds
        ]
        
        result = crawler._extract_title(mock_response)
        
        self.assertEqual(result, "Test Article Title")

    def test_extract_title_fallback(self):
        """Test title extraction fallback."""
        crawler = LegalQACrawlerV4()
        mock_response = Mock()
        mock_response.xpath.side_effect = [
            Mock(get=Mock(return_value=None)),  # First selector fails
            Mock(get=Mock(return_value="Fallback Title"))  # Second selector succeeds
        ]
        
        result = crawler._extract_title(mock_response)
        
        self.assertEqual(result, "Fallback Title")

    def test_extract_title_no_title_found(self):
        """Test title extraction when no title found."""
        crawler = LegalQACrawlerV4()
        mock_response = Mock()
        mock_response.xpath.side_effect = [
            Mock(get=Mock(return_value=None)),  # All selectors fail
            Mock(get=Mock(return_value=None))
        ]
        
        result = crawler._extract_title(mock_response)
        
        self.assertEqual(result, "Unknown Title")

    def test_extract_questions(self):
        """Test question extraction from response."""
        crawler = LegalQACrawlerV4()
        mock_response = Mock()
        mock_questions = [Mock(), Mock(), Mock()]
        mock_response.xpath.return_value = mock_questions
        
        result = crawler._extract_questions(mock_response)
        
        self.assertEqual(result, mock_questions)
        self.assertEqual(len(result), 3)

    @patch('legal_qa_crawler.datetime')
    def test_create_article_data(self, mock_datetime):
        """Test article data creation."""
        mock_datetime.now.return_value.strftime.return_value = "20230101_120000"
        mock_datetime.now.return_value.isoformat.return_value = "2023-01-01T12:00:00"
        
        crawler = LegalQACrawlerV4()
        mock_response = Mock()
        mock_response.url = "https://example.com/article"
        
        # Mock _extract_title method
        with patch.object(crawler, '_extract_title', return_value="Test Title"):
            qa_pairs = [QAPair(question="Test?", answers=[])]
            result = crawler._create_article_data(mock_response, qa_pairs)
        
        self.assertEqual(result.id, "20230101_120000")
        self.assertEqual(result.url, "https://example.com/article")
        self.assertEqual(result.title, "Test Title")
        self.assertEqual(result.source, CrawlerConfig.DEFAULT_SOURCE)
        self.assertEqual(result.crawled_at, "2023-01-01T12:00:00")
        self.assertEqual(result.qa_pairs, qa_pairs)

    @patch('legal_qa_crawler.asdict')
    def test_parse_success(self, mock_asdict):
        """Test successful parsing of response."""
        mock_asdict.return_value = {"test": "data"}
        
        crawler = LegalQACrawlerV4()
        mock_response = Mock()
        mock_response.url = "https://example.com/article"
        
        # Mock question elements
        mock_question = Mock()
        
        with patch.object(crawler, '_extract_questions', return_value=[mock_question]), \
             patch.object(crawler, '_extract_title', return_value="Test Title"), \
             patch.object(crawler.qa_extractor, 'extract_qa_pairs') as mock_extract:
            
            # Mock QA extraction
            mock_qa_data = QAPair(
                question="Valid question that is long enough?",
                answers=[{"answer": "Valid answer that is long enough", "contexts": []}]
            )
            mock_extract.return_value = mock_qa_data
            
            # Execute parse method
            result = list(crawler.parse(mock_response))
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], {"test": "data"})
        mock_asdict.assert_called_once()

    def test_parse_no_questions(self):
        """Test parsing when no questions found."""
        crawler = LegalQACrawlerV4()
        mock_response = Mock()
        mock_response.url = "https://example.com/article"
        
        with patch.object(crawler, '_extract_questions', return_value=[]):
            result = list(crawler.parse(mock_response))
        
        self.assertEqual(len(result), 0)

    def test_parse_invalid_qa_pairs(self):
        """Test parsing with invalid QA pairs."""
        crawler = LegalQACrawlerV4()
        mock_response = Mock()
        mock_response.url = "https://example.com/article"
        
        mock_question = Mock()
        
        with patch.object(crawler, '_extract_questions', return_value=[mock_question]), \
             patch.object(crawler.qa_extractor, 'extract_qa_pairs') as mock_extract:
            
            # Mock invalid QA extraction (empty question or answers)
            mock_qa_data = QAPair(question="", answers=[])
            mock_extract.return_value = mock_qa_data
            
            result = list(crawler.parse(mock_response))
        
        self.assertEqual(len(result), 0)


class TestUtilityFunctions(unittest.TestCase):
    """Test cases for utility functions."""

    @patch('legal_qa_crawler.CrawlerProcess')
    def test_create_crawler_process(self, mock_crawler_process):
        """Test crawler process creation."""
        mock_process = Mock()
        mock_crawler_process.return_value = mock_process
        
        result = create_crawler_process('urls.json', 'output.json')
        
        self.assertEqual(result, mock_process)
        mock_crawler_process.assert_called_once()
        mock_process.crawl.assert_called_once_with(LegalQACrawlerV4, urls_file='urls.json')

    @patch('legal_qa_crawler.CrawlerProcess')
    @patch('legal_qa_crawler.LegalQACrawlerV4')
    @patch('legal_qa_crawler.datetime')
    @patch('legal_qa_crawler.os.path.join')
    @patch('legal_qa_crawler.os.path.dirname')
    @patch('legal_qa_crawler.os.path.abspath')
    def test_main_function(self, mock_abspath, mock_dirname, mock_join, 
                          mock_datetime, mock_crawler_class, mock_process_class):
        """Test main function execution."""
        # Setup mocks
        mock_abspath.return_value = '/test/path/script.py'
        mock_dirname.side_effect = lambda x: '/test/path' if 'script.py' in x else '/test'
        mock_join.side_effect = lambda *args: '/'.join(args)
        
        mock_datetime.now.return_value.strftime.return_value = "20230101_120000"
        
        mock_crawler = Mock()
        mock_crawler.slug = 'test-slug'
        mock_crawler_class.return_value = mock_crawler
        
        mock_process = Mock()
        mock_process_class.return_value = mock_process
        
        # Execute main
        main()
        
        # Verify process creation and start
        mock_process_class.assert_called_once()
        mock_process.start.assert_called_once()


if __name__ == '__main__':
    unittest.main(verbosity=2)
