from fastapi import APIRouter, Depends, HTTPException
from main.core.gateways.kafka import Kafka
from main.dependencies.kafka import get_kafka_instance
from scripts.mutual_funds_scraper import MutualFundScraper
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logger import setup_logging  # noqa E

logger = setup_logging()

router = APIRouter()

fund_types = {
    "Bond_Funds": "Bond_Funds",
    "Alternative_Funds": "Alternative_Funds",
    "Equity_US_Index_Funds": "Equity_US_Index_Funds",
    "Equity_US_Actively_Managed_Funds": "Equity_US_Actively_Managed_Funds",
    "Equity_US_Sector_Equity": "Equity_US_Sector_Equity",
    "Equity_US_Thematic": "Equity_US_Thematic",
    "Equity_Non_US_Funds": "Equity_Non_US_Funds",
}


async def scrape_and_send_funds(type_fund: str, server: Kafka):
    if type_fund not in fund_types:
        raise HTTPException(status_code=400, detail="Unsupported fund type.")

    try:
        scraper = MutualFundScraper(type_fund=type_fund)
        json_data = scraper.scrape()
        logger.info(f"Scraped {type_fund} data: {len(json_data)}")

        topic_name = server._topic
        payload = {
            "type": type_fund,
            "data": json_data
        }

        await server.aioproducer.send_and_wait(topic_name, json.dumps(payload).encode("utf-8"))
    except Exception as e:
        await server.aioproducer.stop()
        logger.error(f"Failed to send {type_fund} data: {str(e)}")
        raise e
    return f'{type_fund} scraped data sent successfully'


@router.post("/scrape-and-send/{type_fund}")
async def scrape_and_send(type_fund: str, server: Kafka = Depends(get_kafka_instance)):
    return await scrape_and_send_funds(type_fund, server)
