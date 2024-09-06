# Define variables
$IMAGE_NAME = "hamzalandolsi/data_collection"
$TAG = "latest"  # Or use a specific tag if needed

# Build the Docker image
docker build -t ${IMAGE_NAME}:${TAG} .

# Push the Docker image to Docker Hub
docker push ${IMAGE_NAME}:${TAG}

# Clean up unused Docker images and containers (optional)
docker system prune -f
