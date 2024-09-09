""" This data should be refreshed daily"""

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logger import setup_logging  # noqa E

logger = setup_logging()


def scrape(url="https://tradingeconomics.com/bonds"):
    """Scrape bond data tables using Selenium and return JSON format."""

    def setup_driver(timeout: int = 30) -> webdriver.Edge:
        """Initialize the WebDriver for Edge with a configurable timeout."""
        edge_options = Options()
        edge_options.use_chromium = True
        edge_options.add_argument("--headless")
        edge_options.add_argument("--disable-extensions")
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-dev-shm-usage")
        edge_options.add_argument("--window-size=1920,1080")
        edge_options.add_argument('--blink-settings=imagesEnabled=false')
        edge_options.add_argument("--disable-blink-features=AutomationControlled")
        edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        edge_options.add_argument("--log-level=3")

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

    try:
        driver = setup_driver()
        driver.get(url)
        logger.info(f"Opened URL: {url}")

        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        logger.info("Page loaded.")

        table_xpaths = [
            '/html/body/form/div[4]/div/div/div[1]/div/table',
            '/html/body/form/div[4]/div/div/div[2]/div/table',
            '/html/body/form/div[4]/div/div/div[3]/div/table',
            '/html/body/form/div[4]/div/div/div[4]/div/table',
            '/html/body/form/div[4]/div/div/div[5]/div/table',
            '/html/body/form/div[4]/div/div/div[6]/div/table'
        ]

        scraped_data = []

        for i, xpath in enumerate(table_xpaths):
            logger.info(f"Processing table {i+1} with XPath: {xpath}")

            try:
                table = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
            except Exception as e:
                logger.error(f"Table {i+1} not found. Skipping... Error: {e}")
                continue

            headers = ["", 'Country', 'Yield', 'Day', 'Weekly', 'Monthly', 'YoY', 'Date']

            rows = table.find_elements(By.XPATH, './/tr')
            for row in rows:
                cells = row.find_elements(By.XPATH, './/td')
                row_data = [cell.text for cell in cells]
                if row_data:
                    scraped_data.append(dict(zip(headers, row_data)))

        driver.quit()

        if scraped_data:
            return json.dumps(scraped_data)
        else:
            return json.dumps({"error in bonds_scraper": "No tables found or data extracted, scrape function for bonds crashed"})

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return json.dumps({"error in bonds_scraper": str(e)})
