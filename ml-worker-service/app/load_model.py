import joblib
import os
import time

MODEL_PATH = "/models/churn_model.pkl"

def load_model():
    print("[ml-service-worker] | Loading model from shared volume...")

    while True:
        if os.path.exists(MODEL_PATH):
            try:
                model = joblib.load(MODEL_PATH)
                print("[ml-service-worker] | Model loaded successfully!")
                return model
            except Exception as e:
                print("[ml-service-worker] | Model exists but not ready yet...")
                print("Error:", e)

        else:
            print("[ml-service-worker] | Model not found. Waiting for training container...")

        time.sleep(10)