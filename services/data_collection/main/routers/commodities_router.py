from fastapi import APIRouter, Depends, HTTPException
from main.core.gateways.kafka import Kafka
from main.dependencies.kafka import get_kafka_instance
from scripts.commodities import CommoditiesScraper
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logger import setup_logging  # noqa E

logger = setup_logging()

router = APIRouter()

commodity_types = {
    'WTI': 'WTI',
    'BRENT': 'BRENT',
    'NATURAL_GAS': 'NATURAL_GAS',
    'COPPER': 'COPPER',
    'COTTON': 'COTTON',
    'SUGAR': 'SUGAR',
    'COFFEE': 'COFFEE'
}


async def scrape_and_send_commodities(commodity_type: str, server: Kafka):
    if commodity_type not in commodity_types:
        raise HTTPException(status_code=400, detail="Unsupported commodity type.")

    try:
        scraper = CommoditiesScraper(commodity_type=commodity_type)
        json_data = scraper.scrape()
        logger.info(f"Scraped {commodity_type} data: {len(json_data)}")

        topic_name = server._topic
        payload = {
            "type": commodity_type,
            "data": json_data
        }

        await server.aioproducer.send_and_wait(topic_name, json.dumps(payload).encode("utf-8"))
    except Exception as e:
        await server.aioproducer.stop()
        logger.error(f"Failed to send {commodity_type} data: {str(e)}")
        raise e
    return f'{commodity_type} scraped data sent successfully'


@router.post("/scrape-and-send/{commodity_type}")
async def scrape_and_send(commodity_type: str, server: Kafka = Depends(get_kafka_instance)):
    return await scrape_and_send_commodities(commodity_type, server)
