from silver import initialize_spark, process_funds_data

if __name__ == "__main__":
    spark = initialize_spark()
    file_path = "Equity_US_Index_Funds_data.json"

    equity_us_index_funds = process_funds_data(file_path, spark)

    equity_us_index_funds.show(truncate=False)
