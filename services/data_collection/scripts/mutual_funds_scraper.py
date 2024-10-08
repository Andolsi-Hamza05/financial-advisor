from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from bs4 import BeautifulSoup
import time
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logger import setup_logging  # noqa E

logger = setup_logging()


class MutualFundScraper:
    def __init__(self, type_fund: str):
        self.logger = setup_logging()
        self.config = self.load_config('./config/config_mutual_funds.json')
        self.type_fund = type_fund
        self.driver = self.setup_driver()
        self.wait = WebDriverWait(self.driver, 60)

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

    def setup_driver(self) -> webdriver.Edge:
        """Initialize the WebDriver."""
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

        if os.getenv('KUBERNETES_SERVICE_HOST'):
            driver_path = "/app/config/msedgedriver"
        else:
            driver_path = "./config/msedgedriver"

        if os.name == 'nt':
            service = Service(os.path.abspath(driver_path) + ".exe")
        else:
            service = Service(os.path.abspath(driver_path))

        driver = webdriver.Edge(service=service, options=edge_options)
        driver.implicitly_wait(30)
        logger.info("WebDriver initialized successfully.")
        return driver

    def extract_row_data(self, row, columns_names) -> dict:
        """Extract data from a single row in the table."""
        try:
            name = row.find('th').find('a').text.strip()
            symbol = row.find('th').find('div').text.strip()
            columns = row.find_all('td')
            d = {
                'name': name,
                'symbol': symbol
                }
            i = 0
            for column_name in columns_names:
                d[column_name] = columns[i].text.strip()
                i += 1

            return d

        except Exception as e:
            logger.error(f"Failed to extract data from row: {e}")
            return None

    def scrape_table_data(self, driver: webdriver.Edge, columns_names) -> list:
        """Scrape data from the table."""
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div/div/div[2]/div[3]/section/div[3]/main/section/div[1]/section/div[1]/div/table/tbody/tr[1]'))
            )
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            time.sleep(1)
            rows = soup.find('tbody').find_all('tr')
            return [self.extract_row_data(row, columns_names) for row in rows if self.extract_row_data(row, columns_names)]
        except Exception as e:
            logger.error(f"Failed to scrape table data: {e}")
            return []

    def click_next_button(self, driver: webdriver.Edge) -> bool:
        """Click the 'Next' button to navigate to the next page."""
        try:
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div/div/div[2]/div[3]/section/div[3]/main/section/div[1]/section/div[3]/nav/div[2]/button[2]'))
            )
            next_button.click()
            return True
        except:  # noqa
            logger.warning("No more pages to navigate.")
            return False

    def navigate_to_url(self, driver: webdriver.Edge, url: str):
        """Navigate to the specified URL."""
        try:
            driver.get(url)
            logger.info(f"Navigated to {url}")
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            raise

    def scrape_all_pages(self, url: str, columns_names) -> pd.DataFrame:
        """Scrape all pages for a given URL and return the data as a DataFrame."""
        all_data = []
        self.navigate_to_url(self.driver, url)

        while True:
            page_data = self.scrape_table_data(self.driver, columns_names)
            if not page_data:
                break
            all_data.extend(page_data)
            if not self.click_next_button(self.driver):
                break

        df = pd.DataFrame(all_data)
        return df

    def scrape_dict_urls(self, dict_urls, columns_names):
        all_data = []
        for category, url in dict_urls.items():
            logger.info(f"Scraping {category}")
            data = self.scrape_all_pages(url, columns_names)
            data["category"] = category
            data["fund_type"] = self.type_fund
            all_data.append(data)
        combined_df = pd.concat(all_data, ignore_index=True)
        return combined_df

    def scrape(self):
        if self.type_fund == "Bond_Funds":
            df = self.scrape_dict_urls(self.config[self.type_fund], self.config["Bond_Funds_Columns"])
            df.columns = ["name", "symbol", "medalist_rating", "sec_30_day_yield",
                          "ttm_yield", "average_effective_duration", "total_return_1_year",
                          "total_return_3_year", "adjusted_expense_ratio", "asset_under_management",
                          "category", "fund_type"]
            df["region"] = "US Bonds"
            df["Funds repartition Strategy"] = "Bonds"
            jdata = df.to_json(orient="records")
            self.driver.quit()
            return jdata

        elif self.type_fund == "Equity_US_Index_Funds":
            df = self.scrape_dict_urls(self.config["Equity_Funds"]["US Equity"]["Index_Funds"], self.config["Equity_Funds"]["US Equity"]["Index_Funds_Columns"])
            df.columns = ["name", "symbol", "medalist_rating", "sec_30_day_yield",
                          "ttm_yield", "average_effective_duration", "total_return_1_year",
                          "total_return_3_year", "adjusted_expense_ratio", "asset_under_management",
                          "category", "fund_type"]
            df["region"] = "US Equity"
            df["Funds repartition Strategy"] = "Index_Funds"
            jdata = df.to_json(orient="records")
            self.driver.quit()
            return jdata

        elif self.type_fund == "Equity_US_Actively_Managed_Funds":
            df = self.scrape_dict_urls(self.config["Equity_Funds"]["US Equity"]["Actively_Managed_Funds"], self.config["Equity_Funds"]["US Equity"]["Actively_Managed_Funds_Columns"])
            df.columns = ["name", "symbol", "medalist_rating", "sec_30_day_yield",
                          "ttm_yield", "average_effective_duration", "total_return_1_year",
                          "total_return_3_year", "adjusted_expense_ratio", "asset_under_management",
                          "category", "fund_type"]
            df["region"] = "US Equity"
            df["Funds repartition Strategy"] = "Actively_Managed_Funds"
            jdata = df.to_json(orient="records")
            self.driver.quit()
            return jdata

        elif self.type_fund == "Equity_US_Sector_Equity":
            df = self.scrape_dict_urls(self.config["Equity_Funds"]["US Equity"]["Sector_Equity"], self.config["Equity_Funds"]["US Equity"]["Sector_Equity_Columns"])
            df.columns = ["name", "symbol", "Morningstar Rating for Funds", "Medalist Rating", "Adjusted Expense Ratio",
                          "Total Return(1 year)", "Total Return(3 year)",
                          "Total Return(5 years)", "Fund size(AUM)", "category", "fund_type"]
            df["region"] = "US Equity"
            df["Funds repartition Strategy"] = "Sector_Equity"
            jdata = df.to_json(orient="records")
            self.driver.quit()
            return jdata

        elif self.type_fund == "Equity_US_Thematic":
            df = self.scrape_dict_urls(self.config["Equity_Funds"]["US Equity"]["Thematic"], self.config["Equity_Funds"]["US Equity"]["Thematic_Columns"])
            df.columns = ["name", "symbol", "Medalist Rating", "Total Return(1 year)", "Total Return(3 year)",
                          "Morningstar Return Rating", "Morningstar Risk Rating",
                          "Adjusted Expense Ratio", "Fund size(AUM)",
                          "category", "fund_type"]
            df["region"] = "US Equity"
            df["Funds repartition Strategy"] = "Thematic"
            jdata = df.to_json(orient="records")
            self.driver.quit()
            return jdata

        elif self.type_fund == "Equity_Non_US_Funds":
            df = self.scrape_dict_urls(self.config["Equity_Funds"]["International_Equity"], self.config["Equity_Funds"]["International_Equity_Columns"])
            df.columns = ["name", "symbol", "Medalist Rating", "Morningstar Rating for Funds", "Total Return(1 year)",
                          "Total Return(3 year)", "Total Return(5 years)", "Adjusted Expense Ratio",
                          "Fund size(AUM)", "category", "fund_type"]
            df["region"] = "Non US"
            df["Funds repartition Strategy"] = "All"
            jdata = df.to_json(orient="records")
            self.driver.quit()
            return jdata

        elif self.type_fund == "Alternative_Funds":
            df = self.scrape_dict_urls(self.config[self.type_fund], self.config["Alternative_Funds_Columns"])
            df.columns = ["name", "symbol", "Medalist Rating", "Morningstar Rating for Funds", "Total Return(1 year)",
                          "Total Return(3 year)", "Total Return(5 years)", "Adjusted Expense Ratio",
                          "Fund size(AUM)", "category", "fund_type"]
            jdata = df.to_json(orient="records")
            self.driver.quit()
            return jdata

        else:
            logger.error("Unsupported fund type.")
            raise ValueError("Unsupported fund type. Supported fund types are: Bond_Funds, Equity_US_Index_Funds,"
                             "Equity_US_Actively_Managed_Funds, Equity_US_Sector_Equity, Equity_US_Thematic,"
                             "Equity_Non_US_Funds, or Alternative_Funds")
