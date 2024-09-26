import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from bs4 import BeautifulSoup
import concurrent.futures
import sys
import os
from abc import ABC, abstractmethod

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logger import setup_logging  # noqa E

logger = setup_logging()
CACHE_FILE = 'url_cache.json'


class YahooScraper(ABC):
    def __init__(self, config_path: str = 'config/config_stock.json'):
        self.config = self.load_config(config_path)
        self.country = None

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

    def setup_driver(self, timeout: int = 90) -> webdriver.Edge:
        """Initialize the WebDriver for Edge with a configurable timeout."""
        edge_options = Options()
        edge_options.use_chromium = True
        edge_options.add_argument("--headless")
        edge_options.add_argument("--disable-extensions")
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--window-size=1920,1080")
        edge_options.add_argument('--blink-settings=imagesEnabled=false')
        edge_options.add_argument("--disable-dev-shm-usage")
        edge_options.add_argument("--log-level=3")
        edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        edge_options.add_argument("--disable-features=VizDisplayCompositor")
        edge_options.add_argument("--cache-size=104857600")  # 100 MB cache size

        driver_path = "/app/config/msedgedriver" if os.getenv('KUBERNETES_SERVICE_HOST') else "./config/msedgedriver"
        driver_path = driver_path + (".exe" if os.name == 'nt' else "")

        try:
            service = Service(os.path.abspath(driver_path))
            driver = webdriver.Edge(service=service, options=edge_options)
            capabilities = DesiredCapabilities.EDGE.copy()
            capabilities['pageLoadStrategy'] = 'eager'
            driver.implicitly_wait(timeout)
            driver.set_page_load_timeout(timeout)

            logger.info("WebDriver initialized successfully.")
            return driver
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise

    @staticmethod
    def scrape_table_data(wait: WebDriverWait, table_xpath: str) -> list:
        """Scrape data from the table on the current page."""
        logger.info("started scraping table")
        try:
            table_element = wait.until(EC.presence_of_element_located((By.XPATH, table_xpath)))
            table_html = table_element.get_attribute('outerHTML')
            soup = BeautifulSoup(table_html, 'html.parser')
            rows = soup.find_all('tr')
            data = [
                [cell.get_text(strip=True) for cell in row.find_all('td')]
                for row in rows
                if row.find_all('td')
            ]
            logger.info("Table data scraped successfully.")
            return data
        except:  # noqa
            logger.error("Failed to scrape table data")
            return []

    def is_table_present(self, driver: webdriver.Edge, table_xpath_content: str) -> bool:
        """Check if a table is present on the current page."""
        try:
            WebDriverWait(driver, 30, poll_frequency=0.1).until(
                EC.presence_of_element_located((By.XPATH, table_xpath_content))
            )
            return True
        except Exception:
            logger.warning("Table not present after waiting.")
            return False

    def navigate_to_page(self, driver: webdriver.Edge, url: str, iteration: int, initial: int = 0) -> None:
        """Navigate to the specified URL with an updated offset."""
        try:
            updated_url = url.format(i=initial + iteration * 250)
            driver.get(updated_url)
            logger.info(f"Navigated to URL: {updated_url}")
        except Exception as e:
            logger.error(f"Failed to navigate to URL: {url} for iteration {iteration}. Error: {e}")
            raise

    def load_cache(self):
        """Load cached URLs from the file."""
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        return {}

    def save_cache(self, cache):
        """Save the updated cache to the file."""
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f)

    def get_dynamic_url_for_country_sector(self, option_xpaths, sector_option):
        cache = self.load_cache()
        cache_key = f"{self.country.lower()}_{sector_option.lower()}"

        if cache_key in cache:
            logger.info(f"Using cached URL for {sector_option} and {self.country}")
            return cache[cache_key]

        driver = None
        try:
            driver = self.setup_driver()
            driver.get(self.config['page_url'])
            logger.info(f"Navigated to screener web page for {sector_option}")

            add_sector_button = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, self.config['add_sector_button']))
            )
            add_sector_button.click()

            sector_option_xpath = option_xpaths.get(sector_option)
            if sector_option_xpath:
                WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable((By.XPATH, sector_option_xpath))
                ).click()
                logger.info(f"Selected {sector_option} for country {self.country}")
            else:
                logger.error(f"XPath for sector option '{sector_option}' not found.")
                return None

            if self.country.lower() != 'usa':
                # remove usa default option
                WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable((By.XPATH, self.config["country_xpath"]["usa"]))
                ).click()

                # Wait for and click the "Add region" button
                WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable((By.XPATH, self.config['add_region_xpath']))
                ).click()

                WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable((By.XPATH, self.config["country_xpath"][f"{self.country.lower()}"]))
                ).click()
                logger.info(f"Selected the country {self.country.lower()}")

            submit_button = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, self.config['submit_button']))
            )
            submit_button.click()

            WebDriverWait(driver, 30).until(lambda d: d.execute_script('return document.readyState') == 'complete')
            WebDriverWait(driver, 30).until(lambda d: d.current_url != self.config['page_url'])

            generated_url = driver.current_url + "?offset={i}&count=250"
            logger.info(f"Generated URL: {generated_url}")

            cache[cache_key] = generated_url
            self.save_cache(cache)

        except Exception as e:
            logger.error(f"Failed to generate URL for {sector_option}: {e}")
            generated_url = None

        finally:
            if driver:
                driver.quit()

        return generated_url

    def scrape_sequentially_url_with_multiple_offsets(self, url, max_iteration: int = 15):
        all_data = []
        iteration = 0

        with self.setup_driver() as driver:
            wait = WebDriverWait(driver, 60, poll_frequency=0.1)
            self.navigate_to_page(driver, url, 0, 0)

            while (self.is_table_present(driver, self.config['table_verify_content'])) and (iteration < max_iteration):
                try:
                    page_data = self.scrape_table_data(wait, self.config['table_xpath'])
                    iteration += 1
                    all_data.extend(page_data)
                    self.navigate_to_page(driver, url, iteration, 0)
                except:  # noqa
                    logger.warning(f"Finished scraping {url} for iteration {iteration} < {max_iteration}")
                    break
        return all_data

    def scrape_multiple_urls_in_parallel(self, options_xpaths: dict, max_iteration: int) -> list:
        """Scrape multiple URLs in parallel."""

        # Generate URLs in parallel
        def generate_url(sector):
            try:
                url = self.get_dynamic_url_for_country_sector(options_xpaths, sector)
                return sector, url
            except Exception as e:
                logger.error(f"Error fetching URL for sector {sector}: {e}")
                return sector, None

        sector_url_dict = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(options_xpaths)) as executor:
            futures = {executor.submit(generate_url, sector): sector for sector in options_xpaths.keys()}

            for future in concurrent.futures.as_completed(futures):
                sector, url = future.result()
                if url:
                    sector_url_dict[sector] = url
                else:
                    logger.warning(f"No URL generated for sector {sector}")

        logger.info("Finished generating URLs for each sector. Moving to scrape each sector")

        # Scrape data in parallel
        def scrape_url(sector, url):
            try:
                result = self.scrape_sequentially_url_with_multiple_offsets(url, max_iteration)
                for item in result:
                    item.append(sector)
                return result
            except Exception as e:
                logger.error(f"Error scraping data for sector {sector}: {e}")
                return []

        all_data = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(sector_url_dict)) as executor:
            futures = {executor.submit(scrape_url, sector, url): sector for sector, url in sector_url_dict.items()}

            for future in concurrent.futures.as_completed(futures):
                sector = futures[future]
                try:
                    result = future.result()
                    all_data.extend(result)
                except Exception as e:
                    logger.error(f"Error processing results for sector {sector}: {e}")

        return all_data

    def create_dataframe(self, all_data: list) -> pd.DataFrame:
        """Create a DataFrame from the scraped data and add the 'Country' column."""
        columns = ['Symbol', 'Name', 'Real_time_Price', 'Change', '% Change', 'Volume', 'Avg_Vol_3months', 'Market_Cap', 'PE_Ratio', 'Country', 'Sector']
        df = pd.DataFrame(all_data, columns=columns)
        df['Country'] = self.country
        logger.info(f"DataFrame created for {self.country} with shape: {df.shape}.")
        # df.to_csv(f"data/df_{self.country}.csv")
        return df

    @abstractmethod
    def scrape(self) -> dict:
        """Abstract method to encapsulate the scraping process."""
        pass

    def scrape_data(self, heavy_options_key: str, light_options_key: str, max_iteration_heavy: int, max_iteration_light: int) -> dict:
        """Helper method to scrape data for both heavy and light sectors."""
        heavy_data = self.scrape_multiple_urls_in_parallel(self.config[heavy_options_key], max_iteration_heavy)
        light_data = self.scrape_multiple_urls_in_parallel(self.config[light_options_key], max_iteration_light)

        df = self.create_dataframe(heavy_data + light_data)
        jdata = df.to_json(orient="records")
        return jdata


class YahooScraperUSA(YahooScraper):
    def __init__(self, country: str):
        super().__init__()
        self.country = country
        self.max_iteration_heavy = 5
        self.max_iteration_light = 5

    def scrape(self) -> dict:
        """Scrape data for USA and return JSON."""
        jdata = self.scrape_data("heavy_sector_options", "light_sector_options", self.max_iteration_heavy, self.max_iteration_light)
        return jdata


class YahooScraperBigCountries(YahooScraper):
    def __init__(self, country: str):
        super().__init__()
        self.country = country
        self.max_iteration = 5

    def scrape(self) -> dict:
        """Scrape data for specified country and return JSON."""
        jdata = self.scrape_data("heavy_sector_options", "light_sector_options", self.max_iteration, self.max_iteration)
        return jdata


class YahooScraperMediumCountries(YahooScraper):
    def __init__(self, country: str):
        super().__init__()
        self.country = country
        self.max_iteration_1 = 5
        self.max_iteration_2 = 4

    def scrape(self) -> dict:
        """Scrape data for specified country and return JSON."""
        jdata = self.scrape_data("heavy_sector_options", "light_sector_options", self.max_iteration_1, self.max_iteration_2)
        return jdata


class YahooScraperSmallCountries(YahooScraper):
    def __init__(self, country: str):
        super().__init__()
        self.country = country
        self.max_iteration_1 = 4
        self.max_iteration_2 = 3

    def scrape(self) -> dict:
        """Scrape data for specified country and return JSON."""
        jdata = self.scrape_data("heavy_sector_options", "light_sector_options", self.max_iteration_1, self.max_iteration_2)
        return jdata


class YahooScraperFactory:
    @staticmethod
    def create_scraper(country: str) -> YahooScraper:
        """Factory method to create the appropriate scraper based on the country."""
        BigCountries = ['france', 'germany', 'italy']
        MediumCountries = ['austria', 'china', 'uk', 'india']
        SmallCountries = ['australia', 'brazil', 'canada', 'japan', 'south_korea', 'malaysia', 'netherlands', 'sweden',
                          'egypt', 'qatar', 'saudi_arabia', 'south_africa']
        country = country.lower()
        if country == 'usa':
            return YahooScraperUSA(country)
        elif country in BigCountries:
            return YahooScraperBigCountries(country)
        elif country in MediumCountries:
            return YahooScraperMediumCountries(country)
        elif country in SmallCountries:
            return YahooScraperSmallCountries(country)
        else:
            raise ValueError(f"No scraper available for the specified country: {country} \n"
                             f"Available countries are :{['usa']+BigCountries+MediumCountries+SmallCountries}")


if __name__ == "__main__":
    scraper = YahooScraperFactory.create_scraper('uk')
    jdata = scraper.scrape()
    print(len(jdata))
    data_list = json.loads(jdata)

    data_directory = 'data'
    if not os.path.exists(data_directory):
        os.makedirs(data_directory)

    file_name = "uk_data.json"

    file_path = os.path.join(data_directory, file_name)

    with open(file_path, 'w') as json_file:
        for record in data_list:
            json_file.write(json.dumps(record) + '\n')

    print(f"Data saved to {file_path}")
