import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import concurrent.futures
import sys
import os
from abc import ABC, abstractmethod

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logger import setup_logging  # noqa E

logger = setup_logging()


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
            service = Service(os.path.abspath(self.config['driver_path']))
            driver = webdriver.Edge(service=service, options=edge_options)
            driver.implicitly_wait(timeout)
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
            WebDriverWait(driver, 30).until(
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
            driver.set_page_load_timeout(90)
            driver.get(updated_url)
            logger.info(f"Navigated to URL: {updated_url}")
        except Exception as e:
            logger.error(f"Failed to navigate to URL: {url} for iteration {iteration}. Error: {e}")
            raise

    def choose_country(self, driver: webdriver.Edge) -> None:
        """Select a country from the web page by clicking on specified elements."""
        try:
            WebDriverWait(driver, 120).until(
                EC.element_to_be_clickable((By.XPATH, self.config["country_xpath"]["usa"]))
            ).click()
            logger.info("Clicked to remove usa default option.")

            # Wait for and click the "Add region" button
            WebDriverWait(driver, 120).until(
                EC.element_to_be_clickable((By.XPATH, self.config["add_region_xpath"]))
            ).click()
            logger.info("Clicked the 'Add region' button.")

            # Wait for and choose the country
            WebDriverWait(driver, 120).until(
                EC.element_to_be_clickable((By.XPATH, self.config["country_xpath"][f"{self.country}"]))
            ).click()
            logger.info("Selected the country.")

        except Exception as e:
            logger.error(f"An error occurred while choosing the country: {e}")
            raise

    def get_dynamic_url_for_country_sector(self, option_xpaths, sector_option):

        driver = None
        try:
            driver = self.setup_driver(20)
            driver.get(self.config['page_url'])
            logger.info(f"Navigated to screener web page for {sector_option}")

            add_sector_button = WebDriverWait(driver, 120).until(
                EC.element_to_be_clickable((By.XPATH, self.config['add_sector_button']))
            )
            add_sector_button.click()

            basic_materials_checkbox = WebDriverWait(driver, 120).until(
                EC.element_to_be_clickable((By.XPATH, option_xpaths[sector_option]))
            )
            basic_materials_checkbox.click()
            logger.info(f"Clicked on {sector_option} for country {self.country}")

            if self.country.lower() != 'usa':
                WebDriverWait(driver, 120).until(
                    EC.element_to_be_clickable((By.XPATH, self.config["country_xpath"]["usa"]))
                ).click()
                logger.info("Clicked to remove usa default option.")

                # Wait for and click the "Add region" button
                WebDriverWait(driver, 120).until(
                    EC.element_to_be_clickable((By.XPATH, self.config['add_region_xpath']))
                ).click()
                logger.info("Clicked the 'Add region' button.")

                # Wait for and choose the country
                WebDriverWait(driver, 120).until(
                    EC.element_to_be_clickable((By.XPATH, self.config["country_xpath"][f"{self.country.lower()}"]))
                ).click()
                logger.info(f"Selected the country {self.country.lower()}")

            submit_button = WebDriverWait(driver, 120).until(
                EC.element_to_be_clickable((By.XPATH, self.config['submit_button']))
            )
            submit_button.click()
            logger.info(f"submit the choice of {sector_option} for country {self.country}")

            WebDriverWait(driver, 60).until(lambda d: d.execute_script('return document.readyState') == 'complete')

            WebDriverWait(driver, 60).until(lambda d: d.current_url != self.config["page_url"])

            generated_url = driver.current_url + "?offset={i}&count=250"

            logger.info(f"Updated URL: {generated_url}")

        except Exception as e:
            logger.error(f"Failed to interact with web page for sector {sector_option}: {e}")

            # Continue execution even after an error and return the current URL
            generated_url = driver.current_url + "?offset={i}&count=250"

            logger.warning(f"Returning URL after error: {generated_url}")

        finally:
            if driver.session_id is not None:
                driver.quit()
                logger.info(f"Quiting driver for {sector_option} screener")

        return generated_url

    def scrape_sequentially_url_with_multiple_offsets(self, url, max_iteration: int = 15):
        """Scrape data in sequential manner with multiple offsets."""
        driver = self.setup_driver()
        wait = WebDriverWait(driver, 60)

        all_data = []
        iteration = 0
        self.navigate_to_page(driver, url, 0, 0)
        while (self.is_table_present(driver, self.config['table_verify_content'])) and (iteration < max_iteration):
            try:
                page_data = self.scrape_table_data(wait, self.config['table_xpath'])
                iteration += 1
                all_data.extend(page_data)
                self.navigate_to_page(driver, url, iteration, 0)
            except:  # noqa
                driver.quit()
                logger.warning(f"Finished scraping {url} for iteration {iteration} < {max_iteration}")
                break
        if driver is not None and driver.session_id:
            driver.quit()
            logger.warning(f"Finished scraping {url} for iteration {iteration}")
        return all_data

    def scrape_multiple_urls_in_parallel(self, options_xpaths: dict,
                                         max_iteration: int) -> list:

        """Scrape multiple URLs in parallel."""
        sector_url_dict = {}
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(self.get_dynamic_url_for_country_sector, options_xpaths, sector): sector for sector in options_xpaths.keys()}

            for future in concurrent.futures.as_completed(futures):
                sector = futures[future]
                try:
                    sector_url_dict[sector] = future.result()
                except Exception as e:
                    logger.error(f"Error fetching URL for sector {sector}: {e}")

        logger.info("Finished generating urls for each sector. Moving to scrape each sector")
        all_data = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(self.scrape_sequentially_url_with_multiple_offsets, url, max_iteration): sector
                for sector, url in sector_url_dict.items()
            }

            for future in concurrent.futures.as_completed(list(futures.keys())):
                sector = futures[future]
                result = future.result()
                for item in result:
                    item.append(sector)
                all_data.extend(result)

        return all_data

    def create_dataframe(self, all_data: list) -> pd.DataFrame:
        """Create a DataFrame from the scraped data and add the 'Country' column."""
        columns = ['Symbol', 'Name', 'Real_time_Price', 'Change', '% Change', 'Volume', 'Avg_Vol_3months', 'Market_Cap', 'PE_Ratio', 'Country', 'Sector']
        df = pd.DataFrame(all_data, columns=columns)
        df['Country'] = self.country
        logger.info(f"DataFrame created for {self.country} with shape: {df.shape}.")
        df.to_csv(f"data/df_{self.country}.csv")
        return df

    @abstractmethod
    def scrape(self) -> int:
        """Abstract method to encapsulate the scraping process."""
        pass


class YahooScraperUSA(YahooScraper):
    def __init__(self, country: str):
        super().__init__()
        self.country = country
        self.max_iteration_heavy = 14
        self.max_iteration_light = 5

    def scrape(self) -> pd.DataFrame:
        """Scrape data for USA and return a DataFrame."""
        usa_data_1 = self.scrape_multiple_urls_in_parallel(self.config["heavy_sector_options"],
                                                           self.max_iteration_heavy)

        usa_data_2 = self.scrape_multiple_urls_in_parallel(self.config["light_sector_options"],
                                                           self.max_iteration_light)

        df_usa = self.create_dataframe(usa_data_1 + usa_data_2)
        return df_usa


class YahooScraperBigCountries(YahooScraper):
    def __init__(self, country: str):
        super().__init__()
        self.country = country
        self.max_iteration = 6

    def scrape(self) -> pd.DataFrame:
        """Scrape data for specified country and return a DataFrame."""
        data_1 = self.scrape_multiple_urls_in_parallel(self.config["heavy_sector_options"],
                                                       self.max_iteration)

        data_2 = self.scrape_multiple_urls_in_parallel(self.config["light_sector_options"],
                                                       self.max_iteration)

        df = self.create_dataframe(data_1 + data_2)
        return df


class YahooScraperMediumCountries(YahooScraper):
    def __init__(self, country: str):
        super().__init__()
        self.country = country
        self.max_iteration_1 = 5
        self.max_iteration_2 = 4

    def scrape(self) -> pd.DataFrame:
        """Scrape data for specified country and return a DataFrame."""
        data_1 = self.scrape_multiple_urls_in_parallel(self.config["heavy_sector_options"],
                                                       self.max_iteration_1)

        data_2 = self.scrape_multiple_urls_in_parallel(self.config["light_sector_options"],
                                                       self.max_iteration_2)

        df = self.create_dataframe(data_1 + data_2)
        return df


class YahooScraperSmallCountries(YahooScraper):
    def __init__(self, country: str):
        super().__init__()
        self.country = country
        self.country = country
        self.max_iteration_1 = 4
        self.max_iteration_2 = 3

    def scrape(self) -> pd.DataFrame:
        """Scrape data for specified country and return a DataFrame."""
        data_1 = self.scrape_multiple_urls_in_parallel(self.config["heavy_sector_options"],
                                                       self.max_iteration_1)

        data_2 = self.scrape_multiple_urls_in_parallel(self.config["light_sector_options"],
                                                       self.max_iteration_2)

        df = self.create_dataframe(data_1 + data_2)
        return df


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
    scraper = YahooScraperFactory.create_scraper('usa')
    data = scraper.scrape()
    print(data.head())
