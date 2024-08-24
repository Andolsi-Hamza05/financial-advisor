from fastapi import APIRouter, HTTPException
from ..core.gateways.kafka_gateway import KafkaGateway
from ..core.models.equity_us_model import EquityUSFundData

router = APIRouter()

kafka_gateway = KafkaGateway(bootstrap_servers='localhost:9092')


@router.post("/equity_us_funds/")
def produce_equity_us_fund_data(data: EquityUSFundData):
    try:
        kafka_gateway.send_message('equity_us_funds', data.dict())
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
