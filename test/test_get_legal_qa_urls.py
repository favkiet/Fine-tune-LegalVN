"""
Unit tests for get_legal_qa_urls.py

This module contains comprehensive unit tests for the URL extraction functionality
including driver setup, URL scraping, and error handling.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open, call
import json
import tempfile
import os
import sys
from pathlib import Path

# Add the scripts directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from get_legal_qa_urls import (
    get_slug_from_url, 
    setup_driver, 
    setup_firefox_driver, 
    setup_chrome_driver,
    get_page_urls, 
    main
)


class TestGetSlugFromUrl(unittest.TestCase):
    """Test cases for get_slug_from_url function."""

    def test_basic_slug_extraction(self):
        """Test basic slug extraction from URL."""
        url = "https://thuvienphapluat.vn/hoi-dap-phap-luat/thue-phi-le-phi"
        expected = "thue-phi-le-phi"
        result = get_slug_from_url(url)
        self.assertEqual(result, expected)

    def test_slug_with_trailing_slash(self):
        """Test slug extraction with trailing slash."""
        url = "https://thuvienphapluat.vn/hoi-dap-phap-luat/thue-phi-le-phi/"
        expected = "thue-phi-le-phi"
        result = get_slug_from_url(url)
        self.assertEqual(result, expected)

    def test_complex_slug(self):
        """Test slug extraction from complex URL."""
        url = "https://example.com/category/sub-category/final-slug"
        expected = "final-slug"
        result = get_slug_from_url(url)
        self.assertEqual(result, expected)

    def test_invalid_url(self):
        """Test slug extraction from invalid URL."""
        url = "https://example.com/"
        result = get_slug_from_url(url)
        self.assertEqual(result, "example.com")  # This actually extracts the domain

    def test_empty_url(self):
        """Test slug extraction from empty URL."""
        url = ""
        result = get_slug_from_url(url)
        self.assertIsNone(result)


class TestDriverSetup(unittest.TestCase):
    """Test cases for driver setup functions."""

    @patch('get_legal_qa_urls.setup_chrome_driver')
    def test_setup_driver_chrome_default(self, mock_chrome):
        """Test driver setup defaults to Chrome."""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        result = setup_driver()
        
        mock_chrome.assert_called_once()
        self.assertEqual(result, mock_driver)

    @patch('get_legal_qa_urls.setup_chrome_driver')
    def test_setup_driver_chrome_explicit(self, mock_chrome):
        """Test driver setup with explicit Chrome selection."""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        result = setup_driver('chrome')
        
        mock_chrome.assert_called_once()
        self.assertEqual(result, mock_driver)

    @patch('get_legal_qa_urls.setup_firefox_driver')
    def test_setup_driver_firefox(self, mock_firefox):
        """Test driver setup with Firefox selection."""
        mock_driver = Mock()
        mock_firefox.return_value = mock_driver
        
        result = setup_driver('firefox')
        
        mock_firefox.assert_called_once()
        self.assertEqual(result, mock_driver)

    @patch('get_legal_qa_urls.setup_chrome_driver')
    def test_setup_driver_error_handling(self, mock_chrome):
        """Test driver setup error handling."""
        mock_chrome.side_effect = Exception("Driver setup failed")
        
        with self.assertRaises(Exception) as context:
            setup_driver('chrome')
        
        self.assertIn("Driver setup failed", str(context.exception))


class TestChromeDriverSetup(unittest.TestCase):
    """Test cases for Chrome driver setup."""

    @patch('get_legal_qa_urls.webdriver.Chrome')
    @patch('get_legal_qa_urls.ChromeService')
    @patch('get_legal_qa_urls.ChromeDriverManager')
    @patch('get_legal_qa_urls.ChromeOptions')
    def test_chrome_driver_setup(self, mock_options, mock_manager, mock_service, mock_webdriver):
        """Test Chrome driver setup with proper configuration."""
        # Setup mocks
        mock_options_instance = Mock()
        mock_options.return_value = mock_options_instance
        mock_manager.return_value.install.return_value = "/path/to/chromedriver"
        mock_service_instance = Mock()
        mock_service.return_value = mock_service_instance
        mock_driver_instance = Mock()
        mock_webdriver.return_value = mock_driver_instance
        
        result = setup_chrome_driver()
        
        # Verify options configuration
        expected_args = [
            '--headless',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--window-size=1920,1080',
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            '--disable-notifications',
            '--disable-popup-blocking',
            '--disable-extensions'
        ]
        
        for arg in expected_args:
            mock_options_instance.add_argument.assert_any_call(arg)
        
        # Verify driver creation
        mock_service.assert_called_once_with("/path/to/chromedriver")
        mock_webdriver.assert_called_once_with(service=mock_service_instance, options=mock_options_instance)
        mock_driver_instance.set_page_load_timeout.assert_called_once_with(30)
        
        self.assertEqual(result, mock_driver_instance)


class TestFirefoxDriverSetup(unittest.TestCase):
    """Test cases for Firefox driver setup."""

    @patch('get_legal_qa_urls.webdriver.Firefox')
    @patch('get_legal_qa_urls.FirefoxService')
    @patch('get_legal_qa_urls.GeckoDriverManager')
    @patch('get_legal_qa_urls.FirefoxOptions')
    def test_firefox_driver_setup(self, mock_options, mock_manager, mock_service, mock_webdriver):
        """Test Firefox driver setup with proper configuration."""
        # Setup mocks
        mock_options_instance = Mock()
        mock_options.return_value = mock_options_instance
        mock_manager.return_value.install.return_value = "/path/to/geckodriver"
        mock_service_instance = Mock()
        mock_service.return_value = mock_service_instance
        mock_driver_instance = Mock()
        mock_webdriver.return_value = mock_driver_instance
        
        result = setup_firefox_driver()
        
        # Verify options configuration
        mock_options_instance.add_argument.assert_called_with('--headless')
        
        # Verify preferences
        expected_prefs = [
            ('general.useragent.override', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'),
            ('dom.webnotifications.enabled', False),
            ('browser.download.folderList', 2),
            ('browser.download.manager.showWhenStarting', False),
            ('browser.download.useDownloadDir', False),
            ('browser.helperApps.neverAsk.saveToDisk', 'application/pdf'),
            ('media.volume_scale', '0.0'),
            ('app.update.enabled', False)
        ]
        
        for pref_name, pref_value in expected_prefs:
            mock_options_instance.set_preference.assert_any_call(pref_name, pref_value)
        
        # Verify driver creation
        mock_service.assert_called_once_with("/path/to/geckodriver")
        mock_webdriver.assert_called_once_with(service=mock_service_instance, options=mock_options_instance)
        mock_driver_instance.set_page_load_timeout.assert_called_once_with(30)
        
        self.assertEqual(result, mock_driver_instance)


class TestGetPageUrls(unittest.TestCase):
    """Test cases for get_page_urls function."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_driver = Mock()
        self.test_url = "https://example.com/test"

    def test_successful_url_extraction(self):
        """Test successful URL extraction from page."""
        # Mock article elements
        mock_article1 = Mock()
        mock_link1 = Mock()
        mock_link1.get_attribute.return_value = "https://example.com/article1"
        mock_link1.text = "Article 1 Title"
        mock_article1.find_element.return_value = mock_link1

        mock_article2 = Mock()
        mock_link2 = Mock()
        mock_link2.get_attribute.return_value = "https://example.com/article2"
        mock_link2.text = "Article 2 Title"
        mock_article2.find_element.return_value = mock_link2

        self.mock_driver.find_elements.return_value = [mock_article1, mock_article2]

        result = get_page_urls(self.mock_driver, self.test_url)

        expected = [
            {'url': 'https://example.com/article1', 'title': 'Article 1 Title'},
            {'url': 'https://example.com/article2', 'title': 'Article 2 Title'}
        ]

        self.assertEqual(result, expected)
        self.mock_driver.get.assert_called_once_with(self.test_url)

    def test_empty_articles(self):
        """Test handling of page with no articles."""
        self.mock_driver.find_elements.return_value = []

        result = get_page_urls(self.mock_driver, self.test_url)

        self.assertEqual(result, [])

    def test_article_extraction_error(self):
        """Test handling of article extraction errors."""
        mock_article = Mock()
        mock_article.find_element.side_effect = Exception("Element not found")
        self.mock_driver.find_elements.return_value = [mock_article]

        result = get_page_urls(self.mock_driver, self.test_url)

        # Should return empty list when all articles fail
        self.assertEqual(result, [])

    @patch('get_legal_qa_urls.time.sleep')
    def test_timeout_retry(self, mock_sleep):
        """Test retry mechanism on timeout."""
        from selenium.common.exceptions import TimeoutException
        
        # First call raises timeout, second succeeds
        self.mock_driver.get.side_effect = [TimeoutException(), None]
        self.mock_driver.find_elements.return_value = []

        result = get_page_urls(self.mock_driver, self.test_url, retry_count=2)

        self.assertEqual(result, [])
        self.assertEqual(self.mock_driver.get.call_count, 2)
        mock_sleep.assert_called_with(3)

    @patch('get_legal_qa_urls.time.sleep')
    def test_max_retries_exceeded(self, mock_sleep):
        """Test behavior when max retries are exceeded."""
        from selenium.common.exceptions import TimeoutException
        
        self.mock_driver.get.side_effect = TimeoutException("Timeout")

        with self.assertRaises(TimeoutException):
            get_page_urls(self.mock_driver, self.test_url, retry_count=2)

        self.assertEqual(self.mock_driver.get.call_count, 2)


class TestMainFunction(unittest.TestCase):
    """Test cases for main function."""

    @patch('get_legal_qa_urls.argparse.ArgumentParser')
    @patch('get_legal_qa_urls.setup_driver')
    @patch('get_legal_qa_urls.get_page_urls')
    @patch('get_legal_qa_urls.get_slug_from_url')
    @patch('get_legal_qa_urls.os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    @patch('get_legal_qa_urls.json.dump')
    @patch('get_legal_qa_urls.time.sleep')
    def test_main_successful_execution(self, mock_sleep, mock_json_dump, mock_file, 
                                     mock_makedirs, mock_get_slug, mock_get_page_urls, 
                                     mock_setup_driver, mock_parser):
        """Test successful execution of main function."""
        # Setup argument parser mock
        mock_args = Mock()
        mock_args.url = 'https://example.com/test'
        mock_args.max_pages = 3
        mock_args.browser = 'chrome'
        mock_parser.return_value.parse_args.return_value = mock_args

        # Setup other mocks
        mock_driver = Mock()
        mock_setup_driver.return_value = mock_driver
        mock_get_slug.return_value = 'test-slug'
        mock_get_page_urls.return_value = [
            {'url': 'https://example.com/article1', 'title': 'Article 1'}
        ]

        # Execute main function
        with patch('get_legal_qa_urls.os.path.dirname') as mock_dirname, \
             patch('get_legal_qa_urls.os.path.abspath') as mock_abspath, \
             patch('get_legal_qa_urls.os.path.join') as mock_join:
            
            mock_dirname.return_value = '/test/path'
            mock_abspath.return_value = '/test/path/script.py'
            mock_join.side_effect = lambda *args: '/'.join(args)
            
            main()

        # Verify driver setup and cleanup
        mock_setup_driver.assert_called_once_with('chrome')
        mock_driver.quit.assert_called_once()

        # Verify page crawling (first page + 2 additional pages)
        self.assertEqual(mock_get_page_urls.call_count, 3)

        # Verify file operations
        mock_makedirs.assert_called_once()
        mock_json_dump.assert_called_once()

    @patch('get_legal_qa_urls.argparse.ArgumentParser')
    @patch('get_legal_qa_urls.setup_driver')
    def test_main_driver_setup_error(self, mock_setup_driver, mock_parser):
        """Test main function handling driver setup errors."""
        # Setup argument parser mock
        mock_args = Mock()
        mock_args.url = 'https://example.com/test'
        mock_args.max_pages = 1
        mock_args.browser = 'chrome'
        mock_parser.return_value.parse_args.return_value = mock_args

        # Setup driver to raise exception
        mock_setup_driver.side_effect = Exception("Driver setup failed")

        # Should not raise exception (handled internally)
        main()

        mock_setup_driver.assert_called_once_with('chrome')

    @patch('get_legal_qa_urls.argparse.ArgumentParser')
    @patch('get_legal_qa_urls.setup_driver')
    @patch('get_legal_qa_urls.get_page_urls')
    @patch('get_legal_qa_urls.get_slug_from_url')
    def test_main_no_urls_collected(self, mock_get_slug, mock_get_page_urls, 
                                  mock_setup_driver, mock_parser):
        """Test main function when no URLs are collected."""
        # Setup mocks
        mock_args = Mock()
        mock_args.url = 'https://example.com/test'
        mock_args.max_pages = 1
        mock_args.browser = 'chrome'
        mock_parser.return_value.parse_args.return_value = mock_args

        mock_driver = Mock()
        mock_setup_driver.return_value = mock_driver
        mock_get_slug.return_value = 'test-slug'
        mock_get_page_urls.return_value = []  # No URLs found

        main()

        # Verify driver cleanup still happens
        mock_driver.quit.assert_called_once()


if __name__ == '__main__':
    unittest.main(verbosity=2)
