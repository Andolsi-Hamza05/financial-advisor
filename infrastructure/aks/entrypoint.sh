set -x  # Enable script debugging

echo "Starting Kafka setup..."

# Set variables
NAMESPACE="kafka"
KAFKA_URL="https://strimzi.io/install/latest?namespace=kafka"
KAFKA_CR_PATH=infrastructure/aks/kafka
DATA_COLLECTION_DEPLOYMENT=infrastructure/aks/data-collection
FEATURE_SELECTION_DEPLOYMENT=infrastructure/aks/feature-selection
WAIT_TIMEOUT="400s"

echo "Creating namespace $NAMESPACE"
kubectl create namespace $NAMESPACE

echo "Installing Strimzi"
kubectl create -f $KAFKA_URL -n $NAMESPACE

echo "Waiting for Strimzi operator pods to be ready..."
kubectl wait --for=condition=Ready pod -l strimzi.io/kind=cluster-operator -n $NAMESPACE --timeout=$WAIT_TIMEOUT

echo "Applying Kafka CR"
kubectl apply -f $KAFKA_CR_PATH -n $NAMESPACE

echo "Waiting for Kafka cluster to be ready..."
kubectl wait kafka/my-cluster --for=condition=Ready --timeout=$WAIT_TIMEOUT -n $NAMESPACE

echo "Updating Kafka configuration..."
kubectl patch kafka my-cluster -n $NAMESPACE --type='merge' -p='{
  "spec": {
    "kafka": {
      "config": {
        "message.max.bytes": "10485760",
        "max.request.size": "10485760"
      }
    }
  }
}'

echo "Applying data collection manifests"
kubectl apply -f $DATA_COLLECTION_DEPLOYMENT

kubectl create secret generic adls-credentials --from-literal=AZURE_CLIENT_ID=****** --from-literal=AZURE_CLIENT_SECRET=******** --from-literal=AZURE_TENANT_ID=***********
echo "Applying feature selection manifests"
kubectl apply -f $FEATURE_SELECTION_DEPLOYMENT