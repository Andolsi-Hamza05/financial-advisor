FROM python:3.12

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    libnss3 \
    libgconf-2-4 \
    libglib2.0-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxtst6 \
    libxss1 \
    software-properties-common \
    gnupg

# Create the config directory
RUN mkdir -p /app/config

# Download and install Microsoft Edge .deb package
RUN wget https://packages.microsoft.com/keys/microsoft.asc -O- | apt-key add - && \
    wget https://packages.microsoft.com/repos/edge/pool/main/m/microsoft-edge-stable/microsoft-edge-stable_128.0.2739.42-1_amd64.deb -O /app/config/microsoft-edge-stable.deb && \
    apt-get update && \
    apt-get install -y /app/config/microsoft-edge-stable.deb && \
    rm /app/config/microsoft-edge-stable.deb

# Download and install Microsoft Edge WebDriver
RUN wget https://msedgedriver.azureedge.net/128.0.2739.38/edgedriver_linux64.zip -O edgedriver.zip && \
    unzip edgedriver.zip -d /app/config && \
    chmod +x /app/config/msedgedriver && \
    rm edgedriver.zip

# Copy application files
COPY pyproject.toml poetry.lock* /app/
RUN pip install poetry && poetry install --no-dev
COPY . /app/

# Set the entry point with workers
CMD ["poetry", "run", "uvicorn", "main.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

