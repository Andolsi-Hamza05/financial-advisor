import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType
from bronze.custom_enum import EnvironmentVariables as EnvVariables
import os

logging.basicConfig(level=logging.INFO)


def write_stream_to_adls(df, file_system_name, directory_name, storage_account_name, checkpoint_dir):
    try:
        logging.info("Configuring Spark to write stream to ADLS...")

        storage_account_key = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')

        if not storage_account_name or not storage_account_key:
            raise ValueError("Azure Storage environment variables are not set.")

        # Set Hadoop configurations for Azure Data Lake Storage
        hadoop_conf = df._jdf.sparkSession().sparkContext()._jsc.hadoopConfiguration()
        hadoop_conf.set(f"fs.azure.account.key.{storage_account_name}.dfs.core.windows.net", storage_account_key)

        logging.info(f"Writing streaming DataFrame to ADLS at abfss://{file_system_name}@{storage_account_name}.dfs.core.windows.net/{directory_name}/...")

        query = df.writeStream \
            .outputMode("append") \
            .format("json") \
            .option("path", f"abfss://{file_system_name}@{storage_account_name}.dfs.core.windows.net/{directory_name}/") \
            .option("checkpointLocation", checkpoint_dir) \
            .start()

        query.awaitTermination()

        logging.info("Stream successfully written to ADLS.")
    except Exception as e:
        logging.error(f"Error writing streaming DataFrame to ADLS: {e}")
        raise


def initialize_spark():
    """
    Initialize the Spark session with Azure Data Lake credentials.
    """
    spark = SparkSession.builder \
        .appName("FeatureSelectionMicroservice") \
        .config("spark.jars.packages", "io.delta:delta-core_2.12:1.0.0,org.apache.hadoop:hadoop-azure:3.2.0") \
        .config("spark.hadoop.fs.azure.account.key." + os.getenv("AZURE_STORAGE_ACCOUNT_NAME") + ".dfs.core.windows.net", os.getenv("AZURE_STORAGE_ACCOUNT_KEY")) \
        .config("spark.hadoop.fs.abfss.impl", "org.apache.hadoop.fs.azurebfs.AzureBlobFileSystem") \
        .getOrCreate()

    logging.info("Spark session initialized successfully.")
    return spark


def bronze():
    try:
        spark = initialize_spark()

        schema = StructType([
            StructField("type", StringType(), True),
            StructField("data", StringType(), True)
        ])

        # Read stream from Kafka topic
        kafka_df = spark.readStream.format("kafka") \
            .option("kafka.bootstrap.servers", f'{EnvVariables.KAFKA_SERVER.get_env()}:{EnvVariables.KAFKA_PORT.get_env()}') \
            .option("subscribe", EnvVariables.KAFKA_TOPIC_NAME.get_env()) \
            .load()

        kafka_df = kafka_df.selectExpr("CAST(value AS STRING) as json_string")
        df = kafka_df.withColumn("value", from_json(col("json_string"), schema))

        # Extract the fields from JSON
        df = df.select(col("value.type").alias("message_type"), col("value.data").alias("data"))

        logging.info("Kafka stream processed successfully.")

        # Define ADLS details
        file_system_name = "data"
        directory_name = "bronze"
        storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        checkpoint_dir = f"/tmp/checkpoints/{directory_name}"

        # Write stream to ADLS
        write_stream_to_adls(df, file_system_name, directory_name, storage_account_name, checkpoint_dir)

    except Exception as e:
        logging.error(f"Error occurred while processing the stream: {e}")
