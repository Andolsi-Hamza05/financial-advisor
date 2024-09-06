import requests
from bs4 import BeautifulSoup
import json


def scrape_bond_data(url="https://tradingeconomics.com/bonds"):
    # Sending a GET request to the website
    response = requests.get(url)

    # Parsing the HTML content of the page
    soup = BeautifulSoup(response.content, "html.parser")

    # Selecting the table using its XPath-like position
    table = soup.select_one("div.container div div div:nth-of-type(1) table")

    # Checking if the table is found
    if table:
        # Extracting headers
        headers = [header.text.strip() for header in table.find_all("th")]

        # Extracting rows
        rows = table.find_all("tr")[1:]  # Skip the header row
        data = []
        for row in rows:
            columns = [col.text.strip() for col in row.find_all("td")]
            row_data = dict(zip(headers, columns))
            data.append(row_data)

        # Convert the data to JSON format
        json_data = json.dumps(data, indent=4)
        return json_data
    else:
        return json.dumps({"error": "Table not found"})


json_output = scrape_bond_data()
print(json_output)
