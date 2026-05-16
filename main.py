import pandas as pd
from src.engine import run_matching_engine

# LOAD DATA

requests = pd.read_csv("data_samples/requests.csv")
donors = pd.read_csv("data_samples/donors.csv")
donations = pd.read_csv("data_samples/donations.csv")

# DEBUG
# print("\nREQUESTS COLUMNS:\n")
# print(requests.columns.tolist())

# RUN ENGINE

matches = run_matching_engine(requests, donors, donations)

print(matches.head(20))

matches.to_csv("matching_results.csv", index=False)