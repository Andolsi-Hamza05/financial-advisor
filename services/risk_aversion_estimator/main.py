from fastapi import FastAPI, HTTPException
import mlflow
import mlflow.pyfunc
import pandas as pd
from mlflow.tracking import MlflowClient
import joblib

app = FastAPI()

EXPECTED_COLUMNS = [
    'age',
    'education',
    'occupation',
    'kids',
    'income',
    'net_worth',
    'risk',
    'married'
]


def load_latest_model(model_name: str):
    client = MlflowClient()

    # Fetch the latest version of the model
    model_version_info = client.get_latest_versions(model_name, stages=["None", "Staging", "Production"])

    if not model_version_info:
        raise ValueError(f"No model versions found for model '{model_name}'.")

    # Log model version information
    print(f"Latest model versions for {model_name}: {[version.version for version in model_version_info]}")

    # Load the model using pyfunc to support different flavors
    model_uri = f"models:/{model_name}/{model_version_info[0].version}"
    return mlflow.pyfunc.load_model(model_uri)


model_name = "BestModel"
try:
    model = load_latest_model(model_name)
except Exception as e:
    print(f"Error loading model: {e}")
    raise

scaler = joblib.load('scaler.pkl')


@app.post("/predict/")
def predict(data: dict):
    # Create a DataFrame from the incoming data
    df = pd.DataFrame([data])

    # Ensure the DataFrame has the expected columns
    if set(df.columns) != set(EXPECTED_COLUMNS):
        missing_cols = set(EXPECTED_COLUMNS) - set(df.columns)
        extra_cols = set(df.columns) - set(EXPECTED_COLUMNS)
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid input data",
                "missing_columns": list(missing_cols),
                "extra_columns": list(extra_cols)
            }
        )

    # Reorder the DataFrame to match the expected order
    df = df[EXPECTED_COLUMNS]

    # Scale the data
    scaled_data = scaler.transform(df)
    scaled_df = pd.DataFrame(scaled_data, columns=EXPECTED_COLUMNS)

    # Make predictions
    prediction = model.predict(scaled_df)
    return {"risk_aversion_estimate": prediction.tolist()}
