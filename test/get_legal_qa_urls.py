from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException
import traceback
import json
import time
import logging

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


import re

def get_slug_from_url(url):
    match = re.search(r'/([^/]+)/?$', url)
    return match.group(1) if match else None

def setup_driver():
    try:
        # Cấu hình Firefox options
        firefox_options = Options()
        firefox_options.headless = False  # Sử dụng cách cấu hình headless mới
        
        # User agent giả lập
        firefox_options.set_preference('general.useragent.override', 
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0')
        
        # Tắt các thông báo và cảnh báo
        firefox_options.set_preference("dom.webnotifications.enabled", False)
        firefox_options.set_preference("browser.download.folderList", 2)
        firefox_options.set_preference("browser.download.manager.showWhenStarting", False)
        firefox_options.set_preference("browser.download.useDownloadDir", False)
        firefox_options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
        
        # Tắt các tính năng không cần thiết
        firefox_options.set_preference("media.volume_scale", "0.0")
        firefox_options.set_preference("app.update.enabled", False)
        
        # Khởi tạo driver với timeout dài hơn
        service = Service(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=firefox_options)
        driver.set_page_load_timeout(30)
        
        return driver
    except Exception as e:
        logger.error(f"Error setting up Firefox driver: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def get_page_urls(driver, url, retry_count=3):
    urls = []
    for attempt in range(retry_count):
        try:
            logger.info(f"Attempting to load URL: {url} (Attempt {attempt + 1}/{retry_count})")
            driver.get(url)
            
            # Chờ 3 giây cho JavaScript load
            time.sleep(3)
            
            # Sử dụng XPath để lấy các bài viết
            articles = driver.find_elements(By.XPATH, "/html/body/div[5]/div/div[1]/section/article")
            
            for i, article in enumerate(articles, 1):
                try:
                    link_element = article.find_element(By.TAG_NAME, "a")
                    article_url = link_element.get_attribute("href")
                    article_title = link_element.text.strip()
                    if article_url and article_title:
                        urls.append({
                            'url': article_url,
                            'title': article_title
                        })
                        logger.info(f"Article {i}: {article_url}")
                except Exception as e:
                    logger.warning(f"Error extracting article {i} data: {str(e)}")
                    continue
                    
            logger.info(f"Successfully extracted {len(urls)} URLs from page")
            return urls
            
        except TimeoutException:
            logger.warning(f"Timeout on attempt {attempt + 1}")
            if attempt == retry_count - 1:
                logger.error("Max retries reached")
                raise
            time.sleep(5)  # Đợi thêm trước khi thử lại
            
        except Exception as e:
            logger.error(f"Error on attempt {attempt + 1}: {str(e)}")
            logger.error(traceback.format_exc())
            if attempt == retry_count - 1:
                raise
            time.sleep(5)

def main():
    base_url = 'https://thuvienphapluat.vn/hoi-dap-phap-luat/giao-thong-van-tai'
    slug = get_slug_from_url(url)
    max_pages = 25
    all_urls = []
    
    try:
        logger.info("Initializing Firefox driver...")
        driver = setup_driver()
        
        # Crawl trang đầu tiên
        logger.info("Starting crawl of first page...")
        urls = get_page_urls(driver, base_url)
        if urls:
            all_urls.extend(urls)
        
        # Crawl các trang tiếp theo
        for page in range(2, max_pages + 1):
            logger.info(f"Crawling page {page}...")
            page_url = f"{base_url}/?page={page}"
            logger.info(f"{page_url}...")
            time.sleep(3)  # Delay giữa các request
            urls = get_page_urls(driver, page_url)
            if urls:
                all_urls.extend(urls)
            
        # Lưu kết quả
        if all_urls:
            logger.info(f"Saving {len(all_urls)} URLs to file...")
            with open(f'data/json/legal_qa_{slug}_urls.json', 'w', encoding='utf-8') as f:
                json.dump(all_urls, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Total URLs collected: {len(all_urls)}")
            
    except Exception as e:
        logger.error(f"Fatal error occurred: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        try:
            driver.quit()
            logger.info("Browser closed successfully")
        except:
            pass

if __name__ == '__main__':
    main() 