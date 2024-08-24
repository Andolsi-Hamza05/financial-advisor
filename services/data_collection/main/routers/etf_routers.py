from fastapi import APIRouter, HTTPException
from ..core.gateways.kafka_gateway import KafkaGateway
from ..core.models.etf_model import ETFData

router = APIRouter()

kafka_gateway = KafkaGateway(bootstrap_servers='localhost:9092')


@router.post("/etfs/")
def produce_etf_data(data: ETFData):
    try:
        kafka_gateway.send_message('etfs', data.model_dump())
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
