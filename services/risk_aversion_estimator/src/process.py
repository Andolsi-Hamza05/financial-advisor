import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib


def process():
    data = pd.read_csv("data/risktolerance.csv").drop(["Unnamed: 0", "LIFECL07", "WSAVED07", "SPENDMOR07"], axis=1)
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
    # Rename the columns according to the new names
    data = data.rename(columns={
        'AGE07': 'age',
        'EDCL07': 'education',
        'MARRIED07': 'married',
        'KIDS07': 'kids',
        'OCCAT107': 'occupation',
        'INCOME07': 'income',
        'RISK07': 'risk',
        'NETWORTH07': 'net_worth'
    })

    # Separate features and target
    X = data.drop("TrueRiskTol", axis=1)
    y = data["TrueRiskTol"]  # Target variable
    X = X[EXPECTED_COLUMNS]

    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Scale the features
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    joblib.dump(scaler, 'scaler.pkl')
    return X_train, X_test, y_train, y_test
