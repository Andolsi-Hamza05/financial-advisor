# Use the base image for Apache Spark with Python support
FROM apache/spark-py:v3.3.2

# Author and version information
LABEL authors="Hamza Landolsi"

# Set environment variables for Delta and Spark
ENV DELTA_SPARK_VERSION="2.3.0"
ENV SPARK_HOME="/opt/spark"
ENV JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"
ENV PYSPARK_PYTHON="/usr/bin/python3"
ENV PYSPARK_DRIVER_PYTHON="/usr/bin/python3"

# Install essential dependencies including Java and Python
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    curl \
    vim \
    openjdk-11-jdk \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Set up PATH for Poetry
ENV PATH="/root/.local/bin:$PATH"

# Add Delta Lake JAR file
RUN curl -L -o /opt/spark/jars/delta-core_2.12-${DELTA_SPARK_VERSION}.jar \
    https://repo1.maven.org/maven2/io/delta/delta-core_2.12/${DELTA_SPARK_VERSION}/delta-core_2.12-${DELTA_SPARK_VERSION}.jar

# Add Hadoop Azure Blob Storage JAR files
RUN curl -L -o /opt/spark/jars/hadoop-azure_2.12-3.3.4.jar \
    https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-azure/3.3.4/hadoop-azure_2.12-3.3.4.jar && \
    curl -L -o /opt/spark/jars/azure-storage-8.8.1.jar \
    https://repo1.maven.org/maven2/com/microsoft/azure/azure-storage/8.8.1/azure-storage-8.8.1.jar && \
    curl -L -o /opt/spark/jars/azure-storage-common-8.8.1.jar \
    https://repo1.maven.org/maven2/com/microsoft/azure/azure-storage-common/8.8.1/azure-storage-common-8.8.1.jar

# Set environment variables for Hadoop
ENV HADOOP_CONF_DIR=/opt/spark/conf

# Set working directory
WORKDIR /opt/spark

# Copy requirements and install Python packages
COPY requirements.txt /opt/spark/
RUN pip install -r requirements.txt

# Copy the application script and configuration
COPY ./bronze /opt/spark/app
COPY ./main.py /opt/spark
COPY log4j.properties /opt/spark/conf/

# Set the entrypoint to run the application directly
CMD ["spark-submit", "--packages", "com.microsoft.azure:azure-storage:8.6.6,org.apache.hadoop:hadoop-azure:3.3.4", "--master", "local[*]", "--deploy-mode", "client", "/opt/spark/main.py"]