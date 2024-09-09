from fastapi import APIRouter, Depends
from main.core.gateways.kafka import Kafka
from main.dependencies.kafka import get_kafka_instance
from scripts.stock_scraper import YahooScraperFactory
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logger import setup_logging  # noqa E

logger = setup_logging()

router = APIRouter()

# List of countries to scrape
COUNTRIES = ['usa', 'france', 'germany', 'italy', 'austria', 'china', 'uk', 'india', 'australia',
             'brazil', 'canada', 'japan', 'south_korea', 'malaysia', 'netherlands', 'sweden',
             'egypt', 'qatar', 'saudi_arabia', 'south_africa']


async def scrape_and_send_stocks(country: str, server: Kafka):
    try:
        scraper = YahooScraperFactory.create_scraper(country)
        json_data = scraper.scrape()
        logger.info(f"Scraped {country} data: {len(json_data)}")

        topic_name = server._topic
        payload = {
            "type": country,
            "data": json_data
        }

        await server.aioproducer.send_and_wait(topic_name, json.dumps(payload).encode("utf-8"))
        return f'{country} scraped data sent successfully'
    except Exception as e:
        logger.error(f"Failed to send {country} data: {str(e)}")
        return f"Failed to scrape {country}: {str(e)}"


@router.post("/scrape-and-send/{country}")
async def scrape_and_send(country: str, server: Kafka = Depends(get_kafka_instance)):
    return await scrape_and_send_stocks(country, server)
