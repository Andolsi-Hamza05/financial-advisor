import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Load configuration from JSON file
def load_config(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


# Initialize Selenium WebDriver for Microsoft Edge
def initialize_driver(driver_path):
    edge_options = EdgeOptions()
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("--headless")
    edge_service = EdgeService(executable_path=driver_path)
    driver = webdriver.Edge(service=edge_service, options=edge_options)
    return driver


# Function to extract data from a page
def extract_data_from_page(driver, wait, xpaths, column_names):
    data = []
    rows = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//tbody/tr")))

    for row in rows:
        try:
            entry = {}
            for name, xpath in zip(column_names, xpaths):
                element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                entry[name] = element.text
            data.append(entry)
        except Exception as e:
            print(f"Error scraping data for row: {e}")
            continue
    return data


# Function to click a tab to navigate pages
def click_tab(driver, wait, tab_xpath):
    tab = wait.until(EC.presence_of_element_located((By.XPATH, tab_xpath)))
    driver.execute_script("arguments[0].click();", tab)


# Main scraping function
config = load_config('config_etf.json')

driver = initialize_driver(config['driver_path'])
wait = WebDriverWait(driver, 40)

# Navigate to the Morningstar ETF screener page
driver.get(config['url'])

# Define page details
pages = config['pages']

# Scrape data from all pages
for page in pages:
    if page['tab_xpath']:
        click_tab(driver, wait, page['tab_xpath'])
    data = extract_data_from_page(driver, wait, page['xpaths'], page['column_names'])
    print(f"\nData from Page {pages.index(page)+1}:")
    for item in data:
        print(item)

driver.quit()
