# Financial Advisor

The **Financial Advisor** application is designed to help investors construct their portfolios based on their preferences, market trends, and asset analysis. First, the AI agent interacts with customers to perform customer profiling and understand their preferences. It send data to deployed machine learning model to get estimation of the risk aversion(tolerance) coefficient. Then based on natural language prompts it chooses assets from the asset data available in the database. For maintaining our database up to date and representing the actual market state and asset related information, we designed a near real world pipeline : It collects real-time data from financial data sources, we ensure only new data is processed, we compute some important metrics do som data validation checks to get the final gold layer. Finally, the chosen assets and the relevant information of the investor such as risk aversion coefficient are sent to portfolio optimization microservice to provide an optimal portfolio and write a detailed reports explaining the choices and some useful visualizations.

---

### Prerequisites

Make sure you have the following installed on your system:

- [Minikube](https://minikube.sigs.k8s.io/docs/start/)
- [Kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
- [Docker](https://docs.docker.com/get-docker/)
- [Strimzi Kafka Operator](https://strimzi.io/) for Kubernetes

## Deploying the data collection, kafka and feature selection into AKS cluster:

To deploy this project into your azure kubernetes cluster, you can simply provision your aks cluster from azure portal, configure the kubectl to point to your newly created cluster. Ensure you create a managed identity and pass the related secrets in the entrypoint bash script where I put `****` (You can also adjust the kubernetes manifests or the strimzi custom resource deployments) then run the following:

```bash
bash infrastructure/aks/entrypoint.sh
```


Once you finished testing your cluster and see the data collected successfully and sent to kafka and consumed and processed to the final destination, you can terminate all what you created inside your cluster by running :

```bash
bash infrastructure/aks/terminate.sh
```

## Deploying the data collection, kafka and feature selection into local minikube cluster:
Alternatively, if you want to test the setup locally you can try running :

```bash
bash infrastructure/minikube/kafka/kafka-setup.sh
```
Then you can apply the data collection and feature selection manifests inside the `infrastructure/minikube/` directory then pick some endpoint triggers (cronjobs to trigger the data collection endpoints) for your testing purposes. Ensure you're not runing out of memory or CPUs or any other constraints/limits locally.