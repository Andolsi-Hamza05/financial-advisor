from pydantic import BaseModel


class StockData(BaseModel):
    symbol: str
    name: str
    real_time_price: float
    change: float
    percent_change: float
    volume: int
    avg_vol_3months: int
    market_cap: float
    pe_ratio: float
    country: str
    sector: str
