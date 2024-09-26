import requests
import os
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# Base URL for the API
BASE_URL = 'https://www.alphavantage.co/query'

# Fetch API key from environment variables
API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')


def fetch_commodity_data(function_param):
    if not API_KEY:
        raise ValueError("API key is missing. Ensure that the ALPHA_VANTAGE_API_KEY environment variable is set.")

    url = f"{BASE_URL}?function={function_param}&interval=monthly&apikey={API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"Error fetching data: {response.status_code} - {response.text}")

    return response.json()


class CommoditiesScraper:
    def __init__(self, commodity_type):
        self.commodity_type = commodity_type.upper()

    def scrape(self):
        data = fetch_commodity_data(self.commodity_type)
        jdata = data.get('data')
        return json.dumps(jdata)


if __name__ == "__main__":
    # Example usage:
    commodity_type = 'BRENT'
    scraper = CommoditiesScraper(commodity_type)
    jdata = scraper.scrape()
    data_list = json.loads(jdata)

    # Create the 'data' directory if it doesn't exist
    data_directory = 'data'
    if not os.path.exists(data_directory):
        os.makedirs(data_directory)

    file_name = "BRENT_data.json"

    file_path = os.path.join(data_directory, file_name)

    # Write each dict to a new line in the JSON file
    with open(file_path, 'w') as json_file:
        for record in data_list:
            json_file.write(json.dumps(record) + '\n')

    print(f"Data saved to {file_path}")
