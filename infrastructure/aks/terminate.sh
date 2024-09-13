set -x  # Enable script debugging

echo "Starting cleaning kafka and data collection resources..."
kubectl -n kafka delete $(kubectl get strimzi -o name -n kafka)
kubectl delete pvc -l strimzi.io/name=my-cluster-kafka -n kafka
kubectl -n kafka delete -f 'https://strimzi.io/install/latest?namespace=kafka'
kubectl delete namespace kafka
kubectl delete -f infrastructure/aks/data-collection
kubectl delete -f infrastructure/aks/feature_selection