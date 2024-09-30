from pydantic import BaseModel, Field


class CheckSpecificMesurableTimebound(BaseModel):
    """Check if the goal is specific, measurable and time specified"""

    goal: str = Field(description="The clearly defined goal of the investor, if not provided return an empty string")
    initial_investment: float = Field(default=0.0, description="The initial amount invested (upfront)")
    monthly_contribution: float = Field(default=0.0, description="The amount of money that the investor is willing to invest periodically(monthly/annually)")
    annual_return: float = Field(default=0.05, description="Expected annual return rate (r)")
    target_value: float = Field(default=0.0, description="The target future value that the investor wants to achieve.")
    time_horizon: int = Field(default=0, description="The time horizon for the investment.")
    is_specific: str = Field(default="False", description="True if the investor's goal is well defined and specified, else False.")
    is_time: str = Field(default="False", description="True if the investor's time horizon is specified, else False.")
    is_measurable: str = Field(default="False", description="True if the investor specifies the initial_investment, monthly_contribution and target_value, else False.")


class CheckAchievable(BaseModel):
    """Check if the goal is specific, measurable and time specified"""

    future_investment_value: float = Field(description="The calculated future worth of the investment in the future")
    is_achievable: str = Field(description="True if the check_achievable function first string returned claims its achievable and False if not.")
