import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import concurrent.futures
import sys
import os
from abc import ABC, abstractmethod

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logger import setup_logging  # noqa E

logger = setup_logging()


class YahooScraper(ABC):
    def __init__(self, config_path: str):
        self.config = self.load_config(config_path)

    @staticmethod
    def setup_driver(path: str, timeout: int = 10) -> webdriver.Edge:
        """Initialize the WebDriver for Edge with a configurable timeout."""
        try:
            edge_options = Options()
            edge_options.use_chromium = True
            service = Service(path)
            driver = webdriver.Edge(service=service, options=edge_options)
            driver.implicitly_wait(timeout)
            logger.info("WebDriver initialized successfully.")
            return driver
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise

    @staticmethod
    def load_config(config_path: str) -> dict:
        """Load configuration from a JSON file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                logger.info("Configuration loaded successfully.")
                return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise

    @staticmethod
    def scrape_table_data(wait: WebDriverWait, table_xpath: str) -> list:
        """Scrape data from the table on the current page."""
        try:
            table = wait.until(EC.presence_of_element_located((By.XPATH, table_xpath)))
            rows = table.find_elements(By.TAG_NAME, "tr")
            data = [
                [cell.text for cell in row.find_elements(By.TAG_NAME, "td")]
                for row in rows if row.find_elements(By.TAG_NAME, "td")
            ]
            logger.info("Table data scraped successfully.")
            return data
        except Exception as e:
            logger.error(f"Failed to scrape table data: {e}")
            return []

    def is_table_present(self, driver: webdriver.Edge, table_xpath_content: str) -> bool:
        """Check if a table is present on the current page."""
        try:
            driver.find_element(By.XPATH, table_xpath_content)
            return True
        except Exception:
            logger.warning("Table not present.")
            return False

    def scrape_url(self, url: str) -> list:
        """Scrape data from a single URL."""
        driver = self.setup_driver(self.config['path'])
        wait = WebDriverWait(driver, self.config.get('timeout', 10))

        try:
            all_data = []
            iteration = 0
            self.navigate_to_page(driver, url, iteration)

            while self.is_table_present(driver, self.config['table_verify_content']):
                page_data = self.scrape_table_data(wait, self.config['table_xpath'])
                all_data.extend(page_data)
                iteration += 1
                self.navigate_to_page(driver, url, iteration)

            logger.info(f"Finished scraping {url}")
            return all_data

        except Exception as e:
            logger.error(f"Error occurred during scraping {url}: {e}")
            return []

        finally:
            driver.quit()

    def scrape_url_in_parallel(self, url, max_iteration=10, initial=0):
        """Scrape data in parallel with multiple offsets."""
        driver = self.setup_driver(self.config['path'])
        wait = WebDriverWait(driver, 1)

        all_data = []
        iteration = 0
        self.navigate_to_page(driver, url, 0, initial)

        while self.is_table_present(driver, self.config['table_verify_content']) and iteration < max_iteration:
            page_data = self.scrape_table_data(wait, self.config['table_xpath'])
            all_data.extend(page_data)
            iteration += 1
            self.navigate_to_page(driver, url, iteration, initial)

        driver.quit()
        return all_data

    def navigate_to_page(self, driver: webdriver.Edge, url: str, iteration: int, initial: int = 0) -> None:
        """Navigate to the specified URL with an updated offset."""
        try:
            updated_url = url.format(i=initial + iteration * 250)
            driver.get(updated_url)
            logger.info(f"Navigated to URL: {updated_url}")
        except Exception as e:
            logger.error(f"Failed to navigate to URL: {updated_url}. Error: {e}")
            raise

    def scrape_multiple_urls(self, urls: list) -> list:
        """Scrape multiple URLs in parallel."""
        all_data = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.scrape_url, url) for url in urls]
            for future in concurrent.futures.as_completed(futures):
                all_data.extend(future.result())
        return all_data

    def scrape_url_with_multiple_offsets(self, url: str, max_iteration: int = 5, initial_offsets: list = [0, 1250, 2500, 3750, 5000, 6250, 7500, 8750]) -> list:
        """Scrape a single URL in parallel with different initial offsets."""

        all_data = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.scrape_url_in_parallel, url, max_iteration, initial) for initial in initial_offsets]
            for future in concurrent.futures.as_completed(futures):
                all_data.extend(future.result())

        return all_data

    def create_dataframe(self, all_data: list) -> pd.DataFrame:
        """Create a DataFrame from the scraped data and add the 'Country' column."""
        columns = ['Symbol', 'Name', 'Real_time_Price', 'Change', '% Change', 'Volume', 'Avg_Vol_3months', 'Market_Cap', 'PE_Ratio', 'Country']
        df = pd.DataFrame(all_data, columns=columns)
        df['Country'] = self.country
        logger.info(f"DataFrame created for {self.country}.")
        return df

    @abstractmethod
    def scrape(self) -> int:
        """Abstract method to encapsulate the scraping process."""
        pass


class YahooScraperUSA(YahooScraper):
    def __init__(self, config_path: str):
        super().__init__(config_path)
        self.country = 'USA'

    def scrape(self) -> pd.DataFrame:
        """Scrape data for USA and return a DataFrame."""
        usa_data = self.scrape_multiple_urls(self.config['urls_usa'])
        df_usa = self.create_dataframe(usa_data)
        return df_usa


class YahooScraperItaly(YahooScraper):
    def __init__(self, config_path: str):
        super().__init__(config_path)
        self.country = 'Italy'

    def scrape(self) -> pd.DataFrame:
        """Scrape data for Italy and return a DataFrame."""
        italy_data = self.scrape_url_with_multiple_offsets(self.config['urls_italy'][0])
        df_italy = self.create_dataframe(italy_data)
        return df_italy


if __name__ == "__main__":
    usa_scraper = YahooScraperUSA('config.json')
    df_usa = usa_scraper.scrape()
    logger.info(f"df_usa with shape {df_usa.shape}")

    italy_scraper = YahooScraperItaly('config.json')
    df_italy = italy_scraper.scrape()
    logger.info(f"df_italy with shape {df_italy.shape}")