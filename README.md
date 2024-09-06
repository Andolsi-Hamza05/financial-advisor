# Financial Advisor

The **Financial Advisor** application interacts with customers to perform customer profiling and understand their preferences. It collects real-time data from financial data sources, selects financial assets, and re-ranks them based on customer profiles. Finally, the application uses Mean-Variance Optimization methods to provide an optimal portfolio.

---

## Kafka & Microservices Setup on Minikube

This guide outlines how to set up a Kafka cluster using Strimzi on a Minikube Kubernetes cluster and deploy the `data_collection` and `feature_selection` microservices.

### Prerequisites

Make sure you have the following installed on your system:

- [Minikube](https://minikube.sigs.k8s.io/docs/start/)
- [Kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
- [Docker](https://docs.docker.com/get-docker/)
- [Strimzi Kafka Operator](https://strimzi.io/) for Kubernetes

### Step 1: Kafka Setup

To set up Kafka in your Minikube cluster, navigate to the Kafka setup directory and run the `kafka-setup.sh` script:

```bash
cd infrastructure/k8s/kafka
chmod +x kafka-setup.sh
./kafka-setup.sh
```

What This Script Does:
Initializes Minikube with the Docker driver.
Sets up the Strimzi Kafka Operator.
Deploys a Kafka cluster (my-cluster).
The setup may take up to 6 minutes to complete. wait until you see something like that :

```bash
Kafka setup completed successfully!
NAME                                          READY   STATUS    RESTARTS   AGE
my-cluster-dual-role-0                        1/1     Running   0          85s
my-cluster-entity-operator-658cd9bf5b-4grlz   2/2     Running   0          22s
strimzi-cluster-operator-7fb8ff4bd-z9mrl      1/1     Running   0          2m28s
```

### Step 2: Deploy Microservices

After Kafka is successfully set up, apply the Kubernetes manifests for the `data_collection` and `feature_selection` microservices:

```bash
kubectl apply -f infrastructure/k8s/data_collection
kubectl apply -f infrastructure/k8s/feature_selection
```

Verifying Microservice Deployment:
Wait about 3 minutes for the microservices to initialize. Check the status of the pods using the following command:

```bash
kubectl get pod
```
You should see both `data_collection` and `feature_selection` pods in the Running state:

```bash
NAME                                READY   STATUS    RESTARTS   AGE
data-collection-94bfc7b78-zcj82     1/1     Running   0          5m7s
feature-selection-559c49c96-6r58z   1/1     Running   0          4m55s
```

### Step 3: Forward Ports to Access the data_collection API and Sending Requests

Once the data_collection microservice is up and running, you can port-forward the service to access it locally:

```bash
kubectl port-forward svc/data-collection 8080:80
```
This command will forward traffic from `localhost:8080` to the `data_collection` service running in Kubernetes.

You can now send POST requests to the `data_collection` service using an API testing tool like Thunder Client or Postman.

Example Endpoint:
```bash
POST http://localhost:8080/producer/scrape-and-send/
```

This will trigger the scrape-and-send process in the `data_collection` microservice.
you can check the logs of `data_collection` pod to see the logs of the script running successfully and scraping data as intended and the logs of `feature_selection` to ensure the data has been consumed from kafka successfully.