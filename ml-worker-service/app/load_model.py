import joblib
import os
import time

MODEL_PATH = "/models/churn_model.pkl"

def load_model():

    print("Loading model from shared volume...")

    while not os.path.exists(MODEL_PATH):
        print("Waiting for model file...")
        time.sleep(2)

    model = joblib.load(MODEL_PATH)

    print("Model loaded successfully!")
    return model