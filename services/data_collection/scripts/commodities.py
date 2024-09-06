import requests

# Base URL for the API
BASE_URL = 'https://www.alphavantage.co/query'

API_KEY = '21GALYBRY655E8HO'


def fetch_commodity_data(function_param):
    url = f"{BASE_URL}?function={function_param}&interval=monthly&apikey={API_KEY}"
    response = requests.get(url)
    return response.json()


def wti_data():
    return fetch_commodity_data('WTI')


def brent_data():
    return fetch_commodity_data('BRENT')


def natural_gas_data():
    return fetch_commodity_data('NATURAL_GAS')


def copper_data():
    return fetch_commodity_data('COPPER')


def cotton_data():
    return fetch_commodity_data('COTTON')


def sugar_data():
    return fetch_commodity_data('SUGAR')


def coffee_data():
    return fetch_commodity_data('COFFEE')


if __name__ == "__main__":
    wti = wti_data()
    print(wti)
