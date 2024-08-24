from pydantic import BaseModel


class ETFData(BaseModel):
    name: str
    symbol: str
    close_price: float
    dividend_yield: float
    ongoing_charge: float
    category: str
    one_day_yield: float
    one_week_return: float
    one_month_yield: float
    three_month_yield: float
    six_month_yield: float
    yield_for_aaj: float
    one_year_return: float
    three_year_annualized_return: float
    five_year_annualized_return: float
    ten_year_annualized_return: float
    entrance_fee: float
    current_charges: float
    manager_seniority: int
    deferred_charges: float
    minimum_initial_investment: float
    asset_under_management: float
    actions_style_matrix: str
    bonds_style_box: str
    average_stock_market_cap: float
    average_credit_quality: str
    morningstar_risk: str
    alpha_3_years: float
    beta_3_years: float
    r2_over_three_years: float
    three_year_standard_deviation: float
    management: str
