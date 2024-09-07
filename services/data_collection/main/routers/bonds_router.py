from fastapi import APIRouter, Depends
from main.core.gateways.kafka import Kafka
from main.dependencies.kafka import get_kafka_instance
from scripts.bonds_scraper import scrape
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logger import setup_logging  # noqa E

logger = setup_logging()

router = APIRouter()


@router.post("/scrape-and-send/bonds")
async def scrape_and_send(server: Kafka = Depends(get_kafka_instance)):
    try:
        json_data = scrape()
        logger.info(f"Scraped data: {len(json_data)}")
        topic_name = server._topic
        payload = {
            "type": "bonds",
            "data": json_data
        }

        await server.aioproducer.send_and_wait(topic_name, json.dumps(payload).encode("utf-8"))
    except Exception as e:
        await server.aioproducer.stop()
        logger.error(f"Failed to send bonds data: {str(e)}")
        raise e
    return 'bonds scraped data sent successfully'
