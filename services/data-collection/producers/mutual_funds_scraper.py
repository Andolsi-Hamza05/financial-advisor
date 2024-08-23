from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from bs4 import BeautifulSoup
import time
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logger import setup_logging  # noqa E

logger = setup_logging()


def setup_driver(driver_path: str, timeout: int = 90) -> webdriver.Edge:
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

        service = Service(os.path.abspath(driver_path))
        driver = webdriver.Edge(service=service, options=edge_options)
        driver.implicitly_wait(timeout)
        logger.info("WebDriver initialized successfully.")
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize WebDriver: {e}")
        raise


def navigate_to_url(driver: webdriver.Edge, url: str):
    """Navigate to the specified URL."""
    try:
        driver.get(url)
        logger.info(f"Navigated to {url}")
    except Exception as e:
        logger.error(f"Failed to navigate to {url}: {e}")
        raise


def extract_row_data(row) -> dict:
    """Extract data from a single row in the table."""
    try:
        name = row.find('th').find('a').text.strip()
        symbol = row.find('th').find('div').text.strip()

        columns = row.find_all('td')
        return {
            'Name': name,
            'Symbol': symbol,
            'Medalist Rating': columns[0].text.strip(),
            'SEC 30-Day Yield': columns[1].text.strip(),
            'TTM Yield': columns[2].text.strip(),
            'Average Effective Duration': columns[3].text.strip(),
            'Total Return 1 year': columns[4].text.strip(),
            'Total Return 3 year': columns[5].text.strip(),
            'Adjusted Expense Ratio': columns[6].text.strip(),
            'Asset Under Management (Fund Size)': columns[7].text.strip()
        }
    except Exception as e:
        logger.error(f"Failed to extract data from row: {e}")
        return None


def scrape_table_data(driver: webdriver.Edge) -> list:
    """Scrape data from the table on the current page."""
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div/div/div[2]/div[3]/section/div[3]/main/section/div[1]/section/div[1]/div/table/tbody/tr[1]'))
        )
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        time.sleep(1)
        rows = soup.find('tbody').find_all('tr')
        return [extract_row_data(row) for row in rows if extract_row_data(row)]
    except Exception as e:
        logger.error(f"Failed to scrape table data: {e}")
        return []


def click_next_button(driver: webdriver.Edge) -> bool:
    """Click the 'Next' button to navigate to the next page, if possible."""
    try:
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div/div/div[2]/div[3]/section/div[3]/main/section/div[1]/section/div[3]/nav/div[2]/button[2]'))
        )
        next_button.click()
        return True
    except:  # noqa
        logger.warning("No more pages to navigate.")
        return False


def scrape_all_pages(driver: webdriver.Edge) -> pd.DataFrame:
    """Scrape all pages and return the data as a DataFrame."""
    all_data = []

    while True:
        page_data = scrape_table_data(driver)
        if not page_data:
            break
        all_data.extend(page_data)
        if not click_next_button(driver):
            break

    data = pd.DataFrame(all_data)
    data.to_csv("data/core-bond-funds.csv")

    return data


def main():
    driver_path = "./config/msedgedriver.exe"
    url = 'https://www.morningstar.com/best-investments/core-bond-funds'

    driver = setup_driver(driver_path)
    try:
        navigate_to_url(driver, url)
        df = scrape_all_pages(driver)
        logger.info(f"scraped successfully data with shape {df.shape}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
