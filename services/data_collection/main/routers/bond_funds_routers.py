from fastapi import APIRouter, Depends
from main.core.gateways.kafka import Kafka
from main.core.models.bond_fund_model import BondFundData
from main.dependencies.kafka import get_kafka_instance
from scripts.mutual_funds_scraper import MutualFundScraper
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logger import setup_logging  # noqa E

logger = setup_logging()

router = APIRouter()


@router.post("/")
async def send(data: BondFundData, server: Kafka = Depends(get_kafka_instance)):
    try:
        topic_name = server._topic
        await server.aioproducer.send_and_wait(topic_name, json.dumps(data.model_dump()).encode("ascii"))
    except Exception as e:
        await server.aioproducer.stop()
        raise e
    return 'Message sent successfully'


@router.post("/scrape-and-send/")
async def scrape_and_send(server: Kafka = Depends(get_kafka_instance)):
    try:
        scraper = MutualFundScraper(type_fund="Bond_Funds")
        json_data = scraper.scrape()
        logger.info(f"Scraped data: {len(json_data)}")
        topic_name = server._topic
        await server.aioproducer.send_and_wait(topic_name, json.dumps(json_data).encode("utf-8"))
    except Exception as e:
        await server.aioproducer.stop()
        raise e
    return 'Scraped data sent successfully'
