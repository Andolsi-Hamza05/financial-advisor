from fastapi import FastAPI
from .routers import (
    etfs_router,
    bond_funds_router,
    equity_us_funds_router,
    equity_international_funds_router,
    stocks_router
)

app = FastAPI()

app.include_router(etfs_router.router, prefix="/api", tags=["ETFs"])
app.include_router(bond_funds_router.router, prefix="/api", tags=["Bond Funds"])
app.include_router(equity_us_funds_router.router, prefix="/api", tags=["Equity US Funds"])
app.include_router(equity_international_funds_router.router, prefix="/api", tags=["Equity International Funds"])
app.include_router(stocks_router.router, prefix="/api", tags=["Stocks"])
