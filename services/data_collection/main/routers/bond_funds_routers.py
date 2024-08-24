from fastapi import APIRouter, HTTPException
from ..core.gateways.kafka_gateway import KafkaGateway
from ..core.models.bond_fund_model import BondFundData

router = APIRouter()

kafka_gateway = KafkaGateway(bootstrap_servers='localhost:9092')


@router.post("/bond_funds/")
def produce_bond_fund_data(data: BondFundData):
    try:
        kafka_gateway.send_message('bond_funds', data.dict())
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
