import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
import pandas as pd
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logger import setup_logging  # noqa E


class ETFScraper:
    def __init__(self, management):
        self.logger = setup_logging()
        self.config = self.load_config('config/config_etf.json')
        self.management = management
        driver_path = os.path.abspath(self.config['driver_path'])
        self.driver = self.initialize_driver(driver_path)
        self.wait = WebDriverWait(self.driver, 60)

    def load_config(self, file_path):
        """Load configuration from a JSON file."""
        with open(file_path, 'r') as file:
            return json.load(file)

    def initialize_driver(self, path):
        """Initialize the WebDriver for Edge with a configurable timeout."""
        try:
            edge_options = Options()
            edge_options.use_chromium = True
            edge_options.add_argument("--headless")
            edge_options.add_argument("--disable-extensions")
            edge_options.add_argument("--disable-gpu")
            edge_options.add_argument("--no-sandbox")
            edge_options.add_argument("--disable-dev-shm-usage")
            edge_options.add_argument("--window-size=1920,1080")
            edge_options.add_argument('--blink-settings=imagesEnabled=false')
            edge_options.add_argument("--log-level=3")  # Disable logs

            service = Service(path)
            driver = webdriver.Edge(service=service, options=edge_options)
            self.logger.info("WebDriver initialized successfully.")
            return driver
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            raise

    def extract_data_from_page(self, xpaths, column_names):
        """Extract data from the current page using provided XPaths."""
        data = []
        rows = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, "//tbody/tr")))

        for row in rows:
            try:
                entry = {}
                for name, xpath in zip(column_names, xpaths):
                    element = row.find_element(By.XPATH, xpath)
                    entry[name] = element.text
                data.append(entry)
            except Exception as e:
                self.logger.error(f"Error scraping data for row: {e}")
                continue
        return data

    def click_tab(self, tab_xpath):
        """Click a tab to navigate to its page."""
        tab = self.wait.until(EC.presence_of_element_located((By.XPATH, tab_xpath)))
        self.driver.execute_script("arguments[0].click();", tab)

    def select_show_50(self):
        """Select '50' from the dropdown to display 50 rows per page."""
        dropdown = self.wait.until(EC.presence_of_element_located((By.ID, "ec-screener-input-page-size-select")))
        select = Select(dropdown)
        select.select_by_value("50")
        time.sleep(3)

    def click_next_button(self):
        """Click the 'Next' button to navigate to the next page."""
        try:
            next_button_xpath = self.config['next_button_xpath']
            next_button = self.wait.until(EC.presence_of_element_located((By.XPATH, next_button_xpath)))

            self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            self.wait.until(EC.element_to_be_clickable((By.XPATH, next_button_xpath)))
            self.driver.execute_script("arguments[0].click();", next_button)
            self.logger.info("Clicked on the 'Next' button successfully.")
            time.sleep(3)
            return True
        except (NoSuchElementException, TimeoutException) as e:
            self.logger.error(f"Error clicking 'Next' button: {e}")
            return False
        except ElementClickInterceptedException as e:
            self.logger.error(f"Element click intercepted, trying JavaScript click: {e}")
            try:
                self.driver.execute_script("arguments[0].click();", next_button)
                self.logger.info("Successfully clicked 'Next' button using JavaScript.")
                return True
            except Exception as js_error:
                self.logger.error(f"JavaScript click also failed: {js_error}")
                return False

    def scrape_tab(self, tab_xpath, page, index):
        """Scrape data from a single tab and its pages."""
        all_data = []
        existing_names = set()

        self.driver.get(self.config['url'][self.management])
        time.sleep(5)
        self.select_show_50()
        time.sleep(3)

        if tab_xpath:
            self.click_tab(tab_xpath)
        self.logger.info(f"Scraping the tab {index}")

        i = 1
        while i < 50:
            data = self.extract_data_from_page(self.config['xpaths'], page['column_names'])

            for row in data:
                if row['Name'] not in existing_names:
                    all_data.append(row)
                    existing_names.add(row['Name'])

            i += 1

            if not self.click_next_button():
                self.logger.info(f"Finished scraping {tab_xpath} for iteration {i-1}")
                break

        self.logger.info(f"Scraping data for tab {index} finished successfully with {len(all_data)} unique rows")
        return all_data

    def put_all_scraped_data_in_df(self, pages):
        all_scraped_data = []

        for index, page in enumerate(pages):
            tab_data = self.scrape_tab(page['tab_xpath'], page, index)

            if not all_scraped_data:
                all_scraped_data = tab_data
            else:
                for existing_record, new_record in zip(all_scraped_data, tab_data):
                    existing_record.update(new_record)

        final_df = pd.DataFrame(all_scraped_data)
        final_df['Management'] = self.management
        self.logger.info(f"Final data shape: {final_df.shape}")
        return final_df

    def scrape(self):
        pages = self.config['pages']
        df = self.put_all_scraped_data_in_df(pages)
        df.to_csv(f"data/df_etf_{self.management}.csv")
        self.driver.quit()


if __name__ == "__main__":
    scraper = ETFScraper("passively managed")
    scraper.scrape()
