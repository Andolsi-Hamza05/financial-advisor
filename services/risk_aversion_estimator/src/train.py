from src.process import process
import mlflow
import mlflow.sklearn
import mlflow.xgboost
import mlflow.catboost
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import logging
import optuna
from sklearn.model_selection import cross_val_score
from xgboost import XGBRegressor
from catboost import CatBoostRegressor
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO)

X_train, X_test, y_train, y_test = process()


def log_model(run_id, model, model_name):
    """Log the model in the MLflow registry if it doesn't already exist."""
    try:
        mlflow.register_model(f"runs:/{run_id}/model", model_name)
        logging.info(f"Model {model} with name {model_name} registered successfully.")
    except Exception as e:
        logging.warning(f"Model {model_name} registration failed: {e}")


def objective_rf(trial):
    n_estimators = trial.suggest_int("n_estimators", 50, 300)
    max_depth = trial.suggest_categorical("max_depth", [None, 10, 20, 30])
    min_samples_split = trial.suggest_int("min_samples_split", 2, 10)
    min_samples_leaf = trial.suggest_int("min_samples_leaf", 1, 4)

    model = RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth,
                                  min_samples_split=min_samples_split, min_samples_leaf=min_samples_leaf, random_state=42)
    return cross_val_score(model, X_train, y_train, n_jobs=-1, scoring='neg_mean_squared_error').mean()


def objective_xgb(trial):
    n_estimators = trial.suggest_int("n_estimators", 50, 300)
    max_depth = trial.suggest_int("max_depth", 3, 10)
    learning_rate = trial.suggest_float("learning_rate", 0.01, 0.3)

    model = XGBRegressor(n_estimators=n_estimators, max_depth=max_depth, learning_rate=learning_rate, random_state=42)
    return cross_val_score(model, X_train, y_train, n_jobs=-1, scoring='neg_mean_squared_error').mean()


def objective_cat(trial):
    n_estimators = trial.suggest_int("n_estimators", 50, 300)
    depth = trial.suggest_int("depth", 3, 10)
    learning_rate = trial.suggest_float("learning_rate", 0.01, 0.3)

    model = CatBoostRegressor(n_estimators=n_estimators, depth=depth, learning_rate=learning_rate, silent=True, random_state=42)
    model.fit(X_train, y_train, eval_set=(X_test, y_test), early_stopping_rounds=10, verbose=False)
    return mean_squared_error(y_test, model.predict(X_test))


best_model = None
best_mse = float('inf')
best_model_name = ""

# RandomForest tuning
with mlflow.start_run() as run_rf:
    logging.info("Starting RandomForest model training and logging...")
    rf_study = optuna.create_study(direction='minimize')
    rf_study.optimize(objective_rf, n_trials=20)
    best_rf_params = rf_study.best_params
    best_rf = RandomForestRegressor(**best_rf_params, random_state=42)
    best_rf.fit(X_train, y_train)
    mse_rf = mean_squared_error(y_test, best_rf.predict(X_test))
    rmse_rf = np.sqrt(mse_rf)

    # Log RandomForest model
    mlflow.log_params({"model_rf": "RandomForest", **best_rf_params})
    mlflow.log_metric("mse_rf", mse_rf)
    mlflow.log_metric("rmse_rf", rmse_rf)
    mlflow.sklearn.log_model(best_rf, "model_rf")
    log_model(run_rf.info.run_id, best_rf, "BestModel_RF")

    if mse_rf < best_mse:
        best_mse = mse_rf
        best_model = best_rf
        best_model_name = "BestModel_RF"

    logging.info("RandomForest model training and logging complete.")

# XGBoost tuning
with mlflow.start_run() as run_xgb:
    logging.info("Starting XGBoost model training and logging...")
    xgb_study = optuna.create_study(direction='minimize')
    xgb_study.optimize(objective_xgb, n_trials=20)
    best_xgb_params = xgb_study.best_params
    best_xgb = XGBRegressor(**best_xgb_params, random_state=42)
    best_xgb.fit(X_train, y_train)
    mse_xgb = mean_squared_error(y_test, best_xgb.predict(X_test))
    rmse_xgb = np.sqrt(mse_xgb)

    # Log XGBoost model
    mlflow.log_params({"model_xgb": "XGBoost", **best_xgb_params})
    mlflow.log_metric("mse_xgb", mse_xgb)
    mlflow.log_metric("rmse_xgb", rmse_xgb)
    mlflow.xgboost.log_model(best_xgb, "model_xgb")
    log_model(run_xgb.info.run_id, best_xgb, "BestModel_XGB")

    if mse_xgb < best_mse:
        best_mse = mse_xgb
        best_model = best_xgb
        best_model_name = "BestModel_XGB"

    logging.info("XGBoost model training and logging complete.")

# CatBoost tuning
with mlflow.start_run() as run_cat:
    logging.info("Starting CatBoost model training and logging...")
    cat_study = optuna.create_study(direction='minimize')
    cat_study.optimize(objective_cat, n_trials=20)
    best_cat_params = cat_study.best_params
    best_cat = CatBoostRegressor(**best_cat_params, silent=True, random_state=42)
    best_cat.fit(X_train, y_train)
    mse_cat = mean_squared_error(y_test, best_cat.predict(X_test))
    rmse_cat = np.sqrt(mse_cat)

    # Log CatBoost model
    mlflow.log_params({"model_cat": "CatBoost", **best_cat_params})
    mlflow.log_metric("mse_cat", mse_cat)
    mlflow.log_metric("rmse_cat", rmse_cat)
    mlflow.catboost.log_model(best_cat, "model_cat")
    log_model(run_cat.info.run_id, best_cat, "BestModel_CAT")

    if mse_cat < best_mse:
        best_mse = mse_cat
        best_model = best_cat
        best_model_name = "BestModel_CAT"

    logging.info("CatBoost model training and logging complete.")

# Log the best overall model
with mlflow.start_run() as run_best:
    logging.info(f"Registering the best overall model: {best_model_name} with MSE: {best_mse}")
    mlflow.log_params({"best_model": best_model_name})
    mlflow.log_metric("best_mse", best_mse)
    mlflow.log_metric("best_rmse", np.sqrt(best_mse))

    # Log and register the overall best model
    mlflow.sklearn.log_model(best_model, "model")
    log_model(run_best.info.run_id, best_model, "BestModel")

logging.info("Completed model training and logging.")
mlflow.end_run()
