import os
import time

DATA_FOLDER = "data"
CHECK_INTERVAL = 5


def watch_for_new_files():
    """Wait until a new CSV file appears"""

    existing_files = set(os.listdir(DATA_FOLDER))

    while True:
        time.sleep(CHECK_INTERVAL)

        current_files = set(os.listdir(DATA_FOLDER))

        new_files = current_files - existing_files

        for file in new_files:
            if file.endswith(".csv"):
                return os.path.join(DATA_FOLDER, file)

import pandas as pd


def load_sales_data(file_path: str) -> pd.DataFrame:

    print(f"Loading file: {file_path}")

    df = pd.read_csv(file_path)

    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")

    df = df.dropna()

    df = df.drop_duplicates()

    print(f"Loaded {len(df)} valid rows")

    return df