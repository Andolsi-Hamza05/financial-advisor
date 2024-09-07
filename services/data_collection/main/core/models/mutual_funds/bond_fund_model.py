from pydantic import BaseModel


class BondFundData(BaseModel):
    name: str
    symbol: str
    medalist_rating: str
    sec_30_day_yield: float
    ttm_yield: float
    average_effective_duration: float
    total_return_1_year: float
    total_return_3_year: float
    adjusted_expense_ratio: float
    asset_under_management: float
    category: str
    fund_type: str
