# Define variables
IMAGE_NAME="hamzalandolsi/feature_selection"
TAG="latest"

# Build the Docker image
docker build -t ${IMAGE_NAME}:${TAG} .

# Push the Docker image to Docker Hub
docker push ${IMAGE_NAME}:${TAG}
