import mlflow


def setup_mlflow():
    tracking_uri = "http://localhost:5000"
    mlflow.set_tracking_uri(tracking_uri)

    # Set up the experiment
    experiment_name = "risk-aversion-estimator"
    mlflow.set_experiment(experiment_name)


if __name__ == "__main__":
    setup_mlflow()
