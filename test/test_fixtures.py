"""
Test fixtures and mock data for Legal QA project tests.

This module contains reusable test fixtures, mock objects, and sample data
that can be used across different test modules to ensure consistency
and reduce code duplication.
"""

import json
from datetime import datetime
from typing import Dict, List, Any
from unittest.mock import Mock


class MockWebDriverFixtures:
    """Mock WebDriver fixtures for URL extraction tests."""
    
    @staticmethod
    def create_mock_driver():
        """Create a mock WebDriver instance."""
        mock_driver = Mock()
        mock_driver.get = Mock()
        mock_driver.find_elements = Mock()
        mock_driver.quit = Mock()
        mock_driver.set_page_load_timeout = Mock()
        return mock_driver
    
    @staticmethod
    def create_mock_article_elements(urls_and_titles: List[tuple]):
        """
        Create mock article elements for testing.
        
        Args:
            urls_and_titles: List of tuples (url, title)
            
        Returns:
            List of mock article elements
        """
        mock_articles = []
        for url, title in urls_and_titles:
            mock_article = Mock()
            mock_link = Mock()
            mock_link.get_attribute.return_value = url
            mock_link.text = title
            mock_article.find_element.return_value = mock_link
            mock_articles.append(mock_article)
        return mock_articles


class JSONDataFixtures:
    """Sample JSON data fixtures for testing data processing."""
    
    @staticmethod
    def get_minimal_article_data() -> Dict[str, Any]:
        """Get minimal valid article data for testing."""
        return {
            "id": "test-article-1",
            "title": "Test Legal Article",
            "url": "https://thuvienphapluat.vn/test-article-1",
            "source": "thuvienphapluat.vn",
            "crawled_at": "2023-01-01T00:00:00",
            "qa_pairs": [
                {
                    "question": "What is the minimum valid question length for testing purposes?",
                    "answers": [
                        {
                            "answer": "This is a valid answer that meets the minimum length requirement for testing purposes and validation.",
                            "contexts": [
                                "This is the first context that provides background information for the answer.",
                                "This is the second context that adds additional supporting information."
                            ]
                        }
                    ]
                }
            ]
        }
    
    @staticmethod
    def get_complete_article_data() -> Dict[str, Any]:
        """Get complete article data with multiple QA pairs for testing."""
        return {
            "id": "test-article-complete",
            "title": "Complete Test Legal Article with Multiple Questions",
            "url": "https://thuvienphapluat.vn/test-article-complete",
            "source": "thuvienphapluat.vn",
            "crawled_at": "2023-01-15T14:30:00",
            "qa_pairs": [
                {
                    "question": "What are the main provisions regarding tax obligations for businesses?",
                    "answers": [
                        {
                            "answer": "Businesses must register for tax purposes within 30 days of establishment and maintain proper accounting records as specified by the tax authority.",
                            "contexts": [
                                "Article 15 of the Tax Administration Law states that all business entities must register with the tax authority.",
                                "Decree 123/2020 specifies the accounting requirements for different types of businesses.",
                                "Circular 78/2021 provides detailed guidelines for tax registration procedures."
                            ]
                        },
                        {
                            "answer": "Monthly tax declarations must be submitted by the 20th of the following month, with penalties applied for late submissions.",
                            "contexts": [
                                "Law on Tax Administration, Article 28 establishes the deadline for monthly declarations.",
                                "Late submission penalties range from 1% to 2% of the tax amount per day of delay."
                            ]
                        }
                    ]
                },
                {
                    "question": "How are penalties calculated for late tax payments in Vietnam?",
                    "answers": [
                        {
                            "answer": "Penalties for late tax payments are calculated at 0.03% per day of the overdue amount, starting from the day after the payment deadline.",
                            "contexts": [
                                "Article 35 of Law on Tax Administration defines the penalty calculation method.",
                                "The penalty rate was updated in 2021 from the previous rate of 0.05% per day.",
                                "Maximum penalty cannot exceed 100% of the original tax amount."
                            ]
                        }
                    ]
                }
            ]
        }
    
    @staticmethod
    def get_invalid_article_data() -> Dict[str, Any]:
        """Get article data with validation issues for testing error handling."""
        return {
            "id": "test-article-invalid",
            "title": "Invalid Test Article",
            "url": "https://thuvienphapluat.vn/test-article-invalid",
            "source": "thuvienphapluat.vn",
            "crawled_at": "2023-01-01T00:00:00",
            "qa_pairs": [
                {
                    "question": "Hi?",  # Too short
                    "answers": [
                        {
                            "answer": "No.",  # Too short
                            "contexts": ["Ok"]  # Too short
                        }
                    ]
                },
                {
                    "question": "",  # Empty
                    "answers": []  # No answers
                },
                {
                    "question": "What is a valid question that should be processed correctly?",
                    "answers": [
                        {
                            "answer": "This is a valid answer that should be processed even when other data is invalid.",
                            "contexts": [
                                "This is valid context that should be included in the processed data.",
                                "Another valid context for the valid answer."
                            ]
                        }
                    ]
                }
            ]
        }
    
    @staticmethod
    def get_multi_article_dataset() -> List[Dict[str, Any]]:
        """Get a dataset with multiple articles for bulk processing tests."""
        return [
            JSONDataFixtures.get_minimal_article_data(),
            JSONDataFixtures.get_complete_article_data(),
            JSONDataFixtures.get_invalid_article_data(),
            {
                "id": "test-article-4",
                "title": "Fourth Test Article",
                "url": "https://thuvienphapluat.vn/test-article-4",
                "source": "thuvienphapluat.vn",
                "crawled_at": "2023-02-01T10:00:00",
                "qa_pairs": [
                    {
                        "question": "What are the requirements for business license renewal in Vietnam?",
                        "answers": [
                            {
                                "answer": "Business licenses must be renewed every 5 years for limited liability companies and every 10 years for joint stock companies, with application submitted 90 days before expiry.",
                                "contexts": [
                                    "Enterprise Law 2020, Article 45 specifies renewal periods for different company types.",
                                    "Decree 01/2021 establishes the 90-day advance application requirement.",
                                    "Required documents include updated business plan and financial statements for the last 3 years."
                                ]
                            }
                        ]
                    }
                ]
            }
        ]


class ScrapyMockFixtures:
    """Mock fixtures for Scrapy-related testing."""
    
    @staticmethod
    def create_mock_response(url: str = "https://example.com/test"):
        """Create a mock Scrapy response object."""
        mock_response = Mock()
        mock_response.url = url
        mock_response.xpath = Mock()
        return mock_response
    
    @staticmethod
    def create_mock_selector(text_content: str = "Test content"):
        """Create a mock Scrapy selector object."""
        mock_selector = Mock()
        mock_selector.xpath.return_value.get.return_value = text_content
        mock_selector.xpath.return_value = Mock(get=Mock(return_value=text_content))
        return mock_selector
    
    @staticmethod
    def create_mock_html_elements():
        """Create mock HTML elements for testing QA extraction."""
        # Mock question element
        question_element = Mock()
        question_element.xpath.side_effect = [
            Mock(get=Mock(return_value="What is the test question that is long enough to pass validation?")),  # Question text
            []  # Following elements (will be set separately)
        ]
        
        # Mock paragraph element (answer)
        paragraph_element = Mock()
        paragraph_element.xpath.side_effect = [
            Mock(get=Mock(return_value='p')),  # Element type
            Mock(get=Mock(return_value="This is a test answer that is long enough to pass all validation requirements."))  # Text content
        ]
        
        # Mock blockquote element (context)
        blockquote_element = Mock()
        blockquote_element.xpath.side_effect = [
            Mock(get=Mock(return_value='blockquote')),  # Element type
            Mock(get=Mock(return_value="This is test context content that provides supporting information."))  # Text content
        ]
        
        # Mock table element
        table_element = Mock()
        table_element.xpath.side_effect = [
            Mock(get=Mock(return_value='table'))  # Element type
        ]
        
        # Mock heading element (stop processing)
        heading_element = Mock()
        heading_element.xpath.side_effect = [
            Mock(get=Mock(return_value='h2'))  # Element type
        ]
        
        return {
            'question': question_element,
            'paragraph': paragraph_element,
            'blockquote': blockquote_element,
            'table': table_element,
            'heading': heading_element
        }


class URLsDataFixtures:
    """Sample URLs data for testing URL extraction functionality."""
    
    @staticmethod
    def get_sample_urls_data() -> List[Dict[str, str]]:
        """Get sample URLs data as would be saved in JSON format."""
        return [
            {
                "url": "https://thuvienphapluat.vn/hoi-dap-phap-luat/thue-phi-le-phi/article-1",
                "title": "Hỏi về nghĩa vụ nộp thuế thu nhập cá nhân"
            },
            {
                "url": "https://thuvienphapluat.vn/hoi-dap-phap-luat/thue-phi-le-phi/article-2", 
                "title": "Quy định về mức phí lệ phí đăng ký kinh doanh"
            },
            {
                "url": "https://thuvienphapluat.vn/hoi-dap-phap-luat/thue-phi-le-phi/article-3",
                "title": "Thủ tục khai báo thuế giá trị gia tăng hàng tháng"
            },
            {
                "url": "https://thuvienphapluat.vn/hoi-dap-phap-luat/thue-phi-le-phi/article-4",
                "title": "Chính sách ưu đãi thuế cho doanh nghiệp nhỏ và vừa"
            },
            {
                "url": "https://thuvienphapluat.vn/hoi-dap-phap-luat/thue-phi-le-phi/article-5",
                "title": "Xử phạt vi phạm về kê khai và nộp thuế"
            }
        ]


class FileSystemMockFixtures:
    """Mock fixtures for file system operations."""
    
    @staticmethod
    def create_mock_path_with_files(files: List[str]):
        """
        Create mock Path object with specified files.
        
        Args:
            files: List of filenames to mock as existing
            
        Returns:
            Mock Path object
        """
        mock_path = Mock()
        mock_files = []
        
        for filename in files:
            mock_file = Mock()
            mock_file.name = filename
            mock_file.stat.return_value.st_mtime = hash(filename) % 10000  # Deterministic mtime
            mock_files.append(mock_file)
        
        mock_path.glob.return_value = mock_files
        return mock_path
    
    @staticmethod
    def create_temp_json_file(data: Dict[str, Any], filename: str = "test_data.json") -> str:
        """
        Create a temporary JSON file with test data.
        
        Args:
            data: Data to write to JSON file
            filename: Name for the temporary file
            
        Returns:
            Path to the temporary file
        """
        import tempfile
        import os
        
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, filename)
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return temp_file


class DataFrameFixtures:
    """Fixtures for pandas DataFrame testing."""
    
    @staticmethod
    def get_sample_questions_data() -> List[Dict[str, Any]]:
        """Get sample questions data for DataFrame testing."""
        return [
            {
                'field_directory': 'thue-phi-le-phi',
                'question_id': 'q-001',
                'article_id': 'art-001',
                'content': 'What are the tax obligations for small businesses?',
                'created_at': '2023-01-01T00:00:00'
            },
            {
                'field_directory': 'thue-phi-le-phi',
                'question_id': 'q-002',
                'article_id': 'art-001',
                'content': 'How to calculate VAT for imported goods?',
                'created_at': '2023-01-01T00:00:00'
            }
        ]
    
    @staticmethod
    def get_sample_answers_data() -> List[Dict[str, Any]]:
        """Get sample answers data for DataFrame testing."""
        return [
            {
                'answer_id': 'ans-001',
                'question_id': 'q-001',
                'content': 'Small businesses must register for tax within 30 days of establishment.',
                'order_index': 1,
                'created_at': '2023-01-01T00:00:00'
            },
            {
                'answer_id': 'ans-002',
                'question_id': 'q-002',
                'content': 'VAT for imported goods is calculated as (CIF value + import duty) × VAT rate.',
                'order_index': 1,
                'created_at': '2023-01-01T00:00:00'
            }
        ]
    
    @staticmethod
    def get_sample_contexts_data() -> List[Dict[str, Any]]:
        """Get sample contexts data for DataFrame testing."""
        return [
            {
                'context_id': 'ctx-001',
                'content': 'Law on Tax Administration, Article 15',
                'created_at': '2023-01-01T00:00:00'
            },
            {
                'context_id': 'ctx-002',
                'content': 'Circular 78/2021 on tax registration procedures',
                'created_at': '2023-01-01T00:00:00'
            }
        ]
    
    @staticmethod
    def get_sample_answer_contexts_data() -> List[Dict[str, Any]]:
        """Get sample answer-context relationships data for DataFrame testing."""
        return [
            {
                'answer_id': 'ans-001',
                'context_id': 'ctx-001',
                'order_index': 1
            },
            {
                'answer_id': 'ans-001',
                'context_id': 'ctx-002',
                'order_index': 2
            }
        ]


class ConfigurationFixtures:
    """Configuration fixtures for testing."""
    
    @staticmethod
    def get_test_file_patterns():
        """Get test filename patterns for extraction testing."""
        return [
            # (filename, expected_slug)
            ('legal_qa_thue-phi-le-phi.json', 'thue-phi-le-phi'),
            ('legal_qa_thue-phi-le-phi_20230101_120000.json', 'thue-phi-le-phi'),
            ('legal_qa_doanh-nghiep_output.json', 'doanh-nghiep'),
            ('legal_qa_lao-dong_v2.json', 'lao-dong'),
            ('legal_qa_complex-slug-name_output_v3_20230201_150000.json', 'complex-slug-name'),
            ('invalid_filename.json', 'unknown'),  # Should return default
            ('legal_qa_.json', 'unknown'),  # Empty slug should return default
        ]
    
    @staticmethod
    def get_test_validation_cases():
        """Get test cases for content validation."""
        return {
            'valid_questions': [
                "What are the main tax obligations for businesses?",
                "How to calculate VAT on imported goods in Vietnam?",
                "What are the penalties for late tax payment submissions?"
            ],
            'invalid_questions': [
                "Hi?",  # Too short
                "",     # Empty
                "   ",  # Whitespace only
                "Test", # Still too short
            ],
            'valid_answers': [
                "Businesses must register for tax purposes within 30 days of establishment.",
                "VAT on imported goods is calculated using the CIF value plus import duties.",
                "Penalties for late tax payments are 0.03% per day of the overdue amount."
            ],
            'invalid_answers': [
                "Yes.",     # Too short
                "",         # Empty
                "No way",   # Too short
                "   OK   ", # Too short after cleaning
            ],
            'valid_contexts': [
                "Article 15 of Tax Law",
                "Decree 123/2020",
                "Supporting regulation text"
            ],
            'invalid_contexts': [
                "",    # Empty
                "Art", # Too short
                "  ",  # Whitespace only
            ]
        }


def cleanup_temp_files(file_paths: List[str]):
    """
    Clean up temporary files created during testing.
    
    Args:
        file_paths: List of file paths to remove
    """
    import os
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass  # Ignore cleanup errors


# Example usage functions for convenience
def get_sample_json_data() -> str:
    """Get sample JSON data as string for testing."""
    data = JSONDataFixtures.get_multi_article_dataset()
    return json.dumps(data, ensure_ascii=False, indent=2)


def get_sample_urls_json() -> str:
    """Get sample URLs data as JSON string for testing."""
    data = URLsDataFixtures.get_sample_urls_data()
    return json.dumps(data, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    # Print sample data for inspection
    print("Sample JSON Article Data:")
    print(get_sample_json_data())
    print("\n" + "="*50 + "\n")
    print("Sample URLs Data:")
    print(get_sample_urls_json())
