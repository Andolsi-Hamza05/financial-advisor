import logging
from json import loads

from app.enum import EnvironmentVariables as EnvVariables
from kafka import KafkaConsumer

# Set up logging
logging.basicConfig(level=logging.INFO)


def main():
    try:
        # Initialize Kafka consumer
        consumer = KafkaConsumer(
            EnvVariables.KAFKA_TOPIC_NAME.get_env(),
            bootstrap_servers=f'{EnvVariables.KAFKA_SERVER.get_env()}:{EnvVariables.KAFKA_PORT.get_env()}',
            value_deserializer=lambda x: loads(x.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
        )
        logging.info('Kafka consumer started. Listening for messages...')

        for message in consumer:
            payload = message.value
            type_fund = payload.get('type')
            data = payload.get('data')
            logging.info("%s:%d:%d: data from %s data=%s" % (
                message.topic, message.partition, message.offset, type_fund, data))
    except Exception as e:
        logging.error('Error occurred while consuming messages: %s', str(e))
