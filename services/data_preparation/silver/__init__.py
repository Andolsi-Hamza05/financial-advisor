from pyspark.sql import SparkSession
from pyspark.sql.functions import regexp_replace, col
import yfinance as yf  # type: ignore
import pandas as pd
from pyspark.sql import Row


def initialize_spark(app_name="equity_us_actively_managed"):
    """Initialize a Spark session."""
    return SparkSession.builder.appName(app_name).getOrCreate()


def load_data(spark, file_path):
    """Load data from a JSON file."""
    df_raw = spark.read.text(file_path)
    return spark.read.json(df_raw.rdd.map(lambda row: row[0]))


def clean_data(df):
    """Clean percentage columns and convert them to floats."""
    df = df.withColumn("adjusted_expense_ratio", regexp_replace(col("adjusted_expense_ratio"), "%", "").cast("float"))

    df = df.dropna(subset=['symbol', 'adjusted_expense_ratio', 'asset_under_management'])
    df = df.dropDuplicates()

    df = df.withColumn('adjusted_expense_ratio', col('adjusted_expense_ratio').cast('float')) \
           .withColumn('asset_under_management', regexp_replace('asset_under_management', ' Mil', '000000')) \
           .withColumn('asset_under_management', col('asset_under_management').cast('float'))

    return df.select(
        'adjusted_expense_ratio',
        'asset_under_management',
        'category',
        'fund_type',
        'name',
        'symbol'
    )


def fetch_symbols(df):
    """Fetch unique symbols from the DataFrame."""
    return set(df.select("symbol").na.drop().distinct().rdd.flatMap(lambda x: x).collect())


def download_historical_data(symbols):
    """Download historical data for a list of symbols."""
    historical_data = {}
    for symbol in symbols:
        try:
            # Download historical data for each symbol
            data = yf.download(symbol, period='1y')
            data['Symbol'] = symbol
            historical_data[symbol] = data
            print(f"Fetched data for {symbol}")
        except Exception as e:
            print(f"Could not fetch data for {symbol}: {e}")
    return historical_data


def calculate_metrics(historical_data):
    """Calculate total return, standard deviation, and Sharpe ratio for each symbol."""
    # Combine all historical data into one DataFrame
    combined_data = pd.concat(historical_data.values(), ignore_index=True)

    results = {}
    for symbol in combined_data['Symbol'].unique():
        symbol_data = combined_data[combined_data['Symbol'] == symbol].copy()

        # Calculate total return, standard deviation, and Sharpe ratio
        beginning_value = symbol_data['Adj Close'].iloc[0]
        ending_value = symbol_data['Adj Close'].iloc[-1]
        total_return = (ending_value - beginning_value) / beginning_value * 100

        symbol_data['Daily Return'] = symbol_data['Adj Close'].pct_change()
        std_dev = symbol_data['Daily Return'].std()
        average_daily_return = symbol_data['Daily Return'].mean()

        risk_free_rate = 0.0  # Assume risk-free rate is 0 for simplicity
        sharpe_ratio = (average_daily_return - risk_free_rate) / std_dev if std_dev != 0 else None

        results[symbol] = {
            'Total Return (%)': total_return,
            'Standard Deviation': std_dev,
            'Sharpe Ratio': sharpe_ratio
        }

    return pd.DataFrame.from_dict(results, orient='index').reset_index().rename(columns={'index': 'Symbol'})


def enrich_data(spark, df_alternative_funds, total_returns_df):
    """Enrich the alternative funds DataFrame with calculated metrics."""

    rows = [Row(**row) for row in total_returns_df.to_dict(orient='records')]

    total_returns_spark = spark.createDataFrame(rows)

    df_enriched = df_alternative_funds.join(
        total_returns_spark,
        df_alternative_funds['symbol'] == total_returns_spark['Symbol'],
        how='left'
    )

    df_enriched = df_enriched.select(
        df_alternative_funds['adjusted_expense_ratio'],
        df_alternative_funds['asset_under_management'],
        df_alternative_funds['category'],
        df_alternative_funds['fund_type'],
        df_alternative_funds['name'],
        df_alternative_funds['symbol'],
        total_returns_spark['Total Return (%)'],
        total_returns_spark['Standard Deviation'],
        total_returns_spark['Sharpe Ratio']
    )

    return df_enriched


def process_funds_data(file_path, spark):
    """Main pipeline to process data, download historical data, and enrich with metrics."""

    df_raw = load_data(spark, file_path)

    # Step 2: Clean the data
    df_cleaned = clean_data(df_raw)

    # Step 3: Fetch unique symbols from the data
    symbols = fetch_symbols(df_cleaned)

    # Step 4: Download historical stock data for each symbol
    historical_data = download_historical_data(symbols)

    # Step 5: Calculate metrics like total return, standard deviation, and Sharpe ratio
    total_returns_df = calculate_metrics(historical_data)

    # Step 6: Enrich the alternative funds DataFrame with calculated metrics
    df_enriched = enrich_data(spark, df_cleaned, total_returns_df)

    return df_enriched
