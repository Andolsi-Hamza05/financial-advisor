import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import concurrent.futures


def setup_driver(path):
    """Initialize the WebDriver for Edge."""
    edge_options = Options()
    edge_options.use_chromium = True
    service = Service(path)
    return webdriver.Edge(service=service, options=edge_options)


def navigate_to_page(driver, url, iteration):
    """Navigate to the specified URL with updated offset."""
    updated_url = url.format(i=iteration * 250)
    driver.get(updated_url)


def scrape_table_data(wait, table_xpath):
    """Scrape data from the table on the current page."""
    table = wait.until(EC.presence_of_element_located((By.XPATH, table_xpath)))
    rows = table.find_elements(By.TAG_NAME, "tr")
    return [[cell.text for cell in row.find_elements(By.TAG_NAME, "td")] for row in rows if row.find_elements(By.TAG_NAME, "td")]


def load_config():
    """Load configuration from a JSON file."""
    with open('config.json', 'r') as f:
        return json.load(f)


def is_table_present(driver):
    """Check if a table is present on the current page."""
    try:
        # Try to find the table using the provided XPath
        driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div[1]/div/div[2]/div/div/div[6]/div/div/section/div/div[2]/div[1]/table/tbody/tr[1]')
        return True
    except:  # noqa:E
        print("Table not present, False returned")
        return False


def scrape_url(url, config):
    driver = setup_driver(config['path'])
    wait = WebDriverWait(driver, 1)

    all_data = []
    iteration = 0
    navigate_to_page(driver, url, 0)

    print(f"Navigated to the url: {url}")
    while is_table_present(driver):
        print(f"There is a table to scrape at offset {iteration * 250}")
        page_data = scrape_table_data(wait, config['table_xpath'])
        all_data.extend(page_data)
        print(f"Data scraped successfully for offset {iteration * 250}")
        iteration += 1
        navigate_to_page(driver, url, iteration)

    driver.quit()
    print(f"Finishied scraping {url}")
    return all_data


def scrape_usa():
    print("Started scraping USA stocks")
    config = load_config()

    all_data = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(scrape_url, url, config) for url in config['urls']]
        for future in concurrent.futures.as_completed(futures):
            all_data.extend(future.result())

    columns = ['Symbol', 'Name', 'Real_time_Price', 'Change', '% Change', 'Volume', 'Avg_Vol_3months', 'Market_Cap', 'PE_Ratio', 'Irrelevant']
    df = pd.DataFrame(all_data, columns=columns)
    return df
