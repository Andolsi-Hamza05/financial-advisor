from fastapi import APIRouter, HTTPException
from ..core.gateways.kafka_gateway import KafkaGateway
from ..core.models.equity_international_model import EquityInternationalFundData

router = APIRouter()

kafka_gateway = KafkaGateway(bootstrap_servers='localhost:9092')


@router.post("/equity_international_funds/")
def produce_equity_international_fund_data(data: EquityInternationalFundData):
    try:
        kafka_gateway.send_message('equity_international_funds', data.dict())
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
