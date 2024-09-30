FROM python:3.12

# Install curl and other necessary utilities
RUN apt-get update && apt-get install -y curl

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Create a directory for the application
WORKDIR /app/

# Copy only the poetry files for faster cache leveraging
COPY pyproject.toml poetry.lock /app/

# Install dependencies using Poetry
RUN poetry install --no-interaction --no-dev

# Copy the rest of the application files
COPY . /app/


# Expose the port for the app
EXPOSE 8000

# Use Uvicorn to run the FastAPI app
ENTRYPOINT ["poetry", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

