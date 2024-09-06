#!/bin/bash

# Set variables
NAMESPACE="kafka"
KAFKA_URL="https://strimzi.io/install/latest?namespace=kafka"
KAFKA_CR_URL="https://strimzi.io/examples/latest/kafka/kraft/kafka-single-node.yaml"
WAIT_TIMEOUT="400s"

# Start Minikube with required resources
minikube start --cpus=4 --memory=6000mb

# Create namespace
kubectl create namespace $NAMESPACE

# Install Strimzi
kubectl create -f $KAFKA_URL -n $NAMESPACE

# Wait for Strimzi pods to be ready
echo "Waiting for Strimzi operator pods to be ready..."
kubectl wait --for=condition=Ready pod -l strimzi.io/kind=cluster-operator -n $NAMESPACE --timeout=$WAIT_TIMEOUT

# Apply Kafka CR
kubectl apply -f $KAFKA_CR_URL -n $NAMESPACE

# Wait for Kafka cluster to be ready
echo "Waiting for Kafka cluster to be ready..."
kubectl wait kafka/my-cluster --for=condition=Ready --timeout=$WAIT_TIMEOUT -n $NAMESPACE

# Check status of all pods in the Kafka namespace
echo "Kafka setup completed successfully!"
kubectl get pods -n $NAMESPACE
