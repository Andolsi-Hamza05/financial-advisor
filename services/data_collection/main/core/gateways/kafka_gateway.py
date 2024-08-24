from kafka import KafkaProducer


class KafkaGateway:
    def __init__(self, bootstrap_servers: str):
        self.producer = KafkaProducer(bootstrap_servers=bootstrap_servers)

    def send_message(self, topic: str, message: dict):
        self.producer.send(topic, value=message)
        self.producer.flush()
