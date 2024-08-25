from pydantic import BaseModel


class EquityInternationalFundData(BaseModel):
    name: str
    symbol: str
    medalist_rating: str
    morningstar_rating_for_funds: str
    total_return_1_year: float
    total_return_3_year: float
    total_return_5_years: float
    adjusted_expense_ratio: float
    fund_size: float
    category: str
    fund_type: str
    region: str
