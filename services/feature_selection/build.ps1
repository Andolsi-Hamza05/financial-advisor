# Define the image name and tag (update these as needed)
$imageName = "hamzalandolsi/feature_selection"
$tag = "latest"

# Build the Docker image
Write-Host "Building the Docker image..."
docker build -t "$($imageName):$tag" .

# Check if the build was successful
if ($LASTEXITCODE -eq 0) {
    Write-Host "Docker image built successfully: $($imageName):$tag"
    
    # Push the image to Docker Hub
    Write-Host "Pushing the Docker image to Docker Hub..."
    docker push "$($imageName):$tag"

    # Check if the push was successful
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Docker image pushed successfully to Docker Hub: $($imageName):$tag"
    } else {
        Write-Host "Failed to push the Docker image to Docker Hub."
        exit 1
    }
} else {
    Write-Host "Failed to build the Docker image."
    exit 1
}
