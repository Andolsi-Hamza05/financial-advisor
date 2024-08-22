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

logger = setup_logging()


def load_config(file_path):
    """Load configuration from a JSON file."""
    with open(file_path, 'r') as file:
        return json.load(file)


def initialize_driver(path):
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
        logger.info("WebDriver initialized successfully.")
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize WebDriver: {e}")
        raise


def extract_data_from_page(driver, wait, xpaths, column_names):
    """Extract data from the current page using provided XPaths."""
    data = []
    rows = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//tbody/tr")))

    for row in rows:
        try:
            entry = {}
            for name, xpath in zip(column_names, xpaths):
                element = row.find_element(By.XPATH, xpath)
                entry[name] = element.text
            data.append(entry)
        except Exception as e:
            logger.error(f"Error scraping data for row: {e}")
            continue
    return data


def click_tab(driver, wait, tab_xpath):
    """Click a tab to navigate to its page."""
    tab = wait.until(EC.presence_of_element_located((By.XPATH, tab_xpath)))
    driver.execute_script("arguments[0].click();", tab)


def select_show_50(driver, wait):
    """Select '50' from the dropdown to display 50 rows per page."""
    time.sleep(5)
    dropdown = wait.until(EC.presence_of_element_located((By.ID, "ec-screener-input-page-size-select")))
    select = Select(dropdown)
    select.select_by_value("50")


def click_next_button(driver, wait):
    """Click the 'Next' button to navigate to the next page."""
    try:
        next_button_xpath = config['next_button_xpath']
        next_button = wait.until(EC.presence_of_element_located((By.XPATH, next_button_xpath)))

        driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
        wait.until(EC.element_to_be_clickable((By.XPATH, next_button_xpath)))
        driver.execute_script("arguments[0].click();", next_button)
        time.sleep(5)
        logger.info("Clicked on the 'Next' button successfully.")
        return True
    except (NoSuchElementException, TimeoutException) as e:
        logger.error(f"Error clicking 'Next' button: {e}")
        return False
    except ElementClickInterceptedException as e:
        logger.error(f"Element click intercepted, trying JavaScript click: {e}")
        try:
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(5)
            logger.info("Successfully clicked 'Next' button using JavaScript.")
            return True
        except Exception as js_error:
            logger.error(f"JavaScript click also failed: {js_error}")
            return False


def scrape_tab(tab_xpath, page, index, management):
    """Scrape data from a single tab and its pages."""
    all_data = []
    existing_names = set()

    driver = initialize_driver(config['driver_path'])
    wait = WebDriverWait(driver, 40)

    driver.get(config['url'][management])
    time.sleep(5)
    select_show_50(driver, wait)
    time.sleep(5)

    if tab_xpath:
        click_tab(driver, wait, tab_xpath)
    logger.info(f"Scraping the tab {index}")

    i = 1
    while i < 5:
        data = extract_data_from_page(driver, wait, config['xpaths'], page['column_names'])

        for row in data:
            if row['Name'] not in existing_names:
                all_data.append(row)
                existing_names.add(row['Name'])

        i += 1

        if not click_next_button(driver, wait):
            logger.info(f"Finished scraping {tab_xpath} for iteration {i-1}")
            break

    driver.quit()
    logger.info(f"Scraping data for tab {index} finished successfully with {len(all_data)} unique rows")
    return all_data


def put_all_scraped_data_in_df(pages, management):
    all_scraped_data = []

    for index, page in enumerate(pages):
        tab_data = scrape_tab(page['tab_xpath'], page, index, management)

        if not all_scraped_data:
            all_scraped_data = tab_data
        else:
            # Update existing records with new columns
            for existing_record, new_record in zip(all_scraped_data, tab_data):
                existing_record.update(new_record)

    final_df = pd.DataFrame(all_scraped_data)
    final_df['Management'] = management
    logger.info(f"Final data shape: {final_df.shape}")
    return final_df


if __name__ == "__main__":
    config = load_config('config_etf.json')
    pages = config['pages']

    df = put_all_scraped_data_in_df(pages, 'passif_managed')
