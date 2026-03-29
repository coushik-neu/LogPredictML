from load_data import watch_for_new_files, load_sales_data
from publish import publish_sale
from generator import start_generator, stop_generator
import os
import time


def main(): 
    print("Waiting for initial dataset...")

    while not os.path.exists("/ready/data_loaded.flag"):
        print("Waiting for data-init to finish...")
        time.sleep(2)

    print("Initial data found. Starting generator...")

    # 1. Load the initial dataset (used for random generation)
    df = load_sales_data("data/SaaS-Sales.csv")

    print("Starting data generator...")
    start_generator(df, publish_sale)

    print("Watching data folder for new CSV files...")

    while True:

        new_file = watch_for_new_files()

        if new_file:
            print(f"New file detected: {new_file}")

            # 2. stop random data generator
            stop_generator()

            # 3. load the new CSV
            new_df = load_sales_data(new_file)

            print(f"Inserting {len(new_df)} rows into database...")

            # 4. insert all rows into postgres
            for _, row in new_df.iterrows():
                publish_sale(row)

            print("Upload completed!")

            # 5. restart generator
            start_generator(df, publish_sale)


if __name__ == "__main__":
    main()