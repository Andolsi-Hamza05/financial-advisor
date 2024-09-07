from pydantic import BaseModel


class AlternativeFundData(BaseModel):
    name: str
    symbol: str
    medalist_rating: str
    morningstar_rating: str
    total_return_1_year: str
    total_return_3_year: str
    total_return_5_year: str
    adjusted_expense_ratio: str
    asset_under_management: str
