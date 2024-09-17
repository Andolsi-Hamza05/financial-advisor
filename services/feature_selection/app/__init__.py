import logging
from json import loads
from pyspark.sql import SparkSession
from app.custom_enum import EnvironmentVariables as EnvVariables
from kafka import KafkaConsumer
from datetime import datetime
import json
import os

# Logging setup
logging.basicConfig(level=logging.INFO)


def write_dataframe_to_adls(df, file_system_name, directory_name, file_path, spark):
    try:
        logging.info("Configuring Spark to write to ADLS...")

        # Retrieve environment variables for Azure Storage
        storage_account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
        storage_account_key = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')

        if not storage_account_name or not storage_account_key:
            raise ValueError("Azure Storage environment variables are not set.")

        # Set Hadoop configurations for Azure Data Lake Storage
        hadoop_conf = spark._jsc.hadoopConfiguration()
        hadoop_conf.set(f"fs.azure.account.key.{storage_account_name}.dfs.core.windows.net", storage_account_key)

        logging.info(f"Writing DataFrame to ADLS path: {file_path}...")

        # Write DataFrame directly to ADLS
        df.write.mode("overwrite").json(f"abfss://{file_system_name}@{storage_account_name}.dfs.core.windows.net/{directory_name}/{file_path}")

        logging.info(f"DataFrame successfully written to ADLS at {file_path}")
    except Exception as e:
        logging.error(f"Error writing DataFrame to ADLS: {e}")
        raise


def initialize_spark():
    """
    Initialize the Spark session with Delta Lake and Azure Data Lake credentials.
    """
    spark = SparkSession.builder \
        .appName("FeatureSelectionMicroservice") \
        .config("spark.jars.packages", "io.delta:delta-core_2.12:1.0.0,org.apache.hadoop:hadoop-azure:3.2.0") \
        .config("spark.hadoop.fs.azure.account.key." + os.getenv("AZURE_STORAGE_ACCOUNT_NAME") + ".dfs.core.windows.net", os.getenv("AZURE_STORAGE_ACCOUNT_KEY")) \
        .config("spark.hadoop.fs.abfss.impl", "org.apache.hadoop.fs.azurebfs.AzureBlobFileSystem") \
        .getOrCreate()

    logging.info("Spark session initialized successfully.")
    return spark


def main():
    try:
        # Initialize Spark
        spark = initialize_spark()

        # Initialize Kafka consumer
        consumer = KafkaConsumer(
            EnvVariables.KAFKA_TOPIC_NAME.get_env(),
            bootstrap_servers=f'{EnvVariables.KAFKA_SERVER.get_env()}:{EnvVariables.KAFKA_PORT.get_env()}',
            value_deserializer=lambda x: loads(x.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
        )
        logging.info('Kafka consumer started. Listening for messages...')

        file_system_name = "data"
        directory_name = "bronze"

        for message in consumer:
            try:
                payload = message.value
                message_type = payload.get('type')
                data = payload.get('data')

                # Log incoming data
                logging.info(f"Received data from Kafka: {message_type}, Data type: {type(data)}")

                jdata = json.loads(data)

                logging.info(f"type of loaded json data : {type(jdata)}")
                df = spark.createDataFrame(jdata)

                logging.info("DataFrame created successfully.")
                current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                file_path = f"{message_type}/{current_timestamp}.json"

                write_dataframe_to_adls(df, file_system_name, directory_name, file_path, spark)

            except Exception as e:
                logging.error(f"Error processing Kafka message: {str(e)}")

    except Exception as e:
        logging.error(f"Error occurred while initializing Kafka consumer or processing messages: {str(e)}")
