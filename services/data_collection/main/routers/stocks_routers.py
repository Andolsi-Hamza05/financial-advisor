from fastapi import APIRouter, HTTPException
from ..core.gateways.kafka_gateway import KafkaGateway
from ..core.models.stock_model import StockData

router = APIRouter()

kafka_gateway = KafkaGateway(bootstrap_servers='localhost:9092')


@router.post("/stocks/")
def produce_stock_data(data: StockData):
    try:
        kafka_gateway.send_message('stocks', data.dict())
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
