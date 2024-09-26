FROM python:3.9-slim

# Set working directory inside the container
WORKDIR /app

# Copy the requirements.txt file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the working directory
COPY . .

# Expose port 8000 for FastAPI
EXPOSE 8000

# Command to run the FastAPI server
CMD ["bash", "-c", "python src/train.py && uvicorn main:app --host 0.0.0.0 --port 8000"]
