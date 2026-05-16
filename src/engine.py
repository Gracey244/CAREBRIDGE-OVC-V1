import pandas as pd
from src.scoring import compute_priority_score
from src.matching import match_donors_to_request

# MATCHING ENGINE

def run_matching_engine(requests, donors, donations):

    # Step 1: Identify busy donors
    active_donations = donations[donations["status"] == "Pending"]
    busy_donors = set(active_donations["donor_id"])

    donors["is_available"] = ~donors["donor_id"].isin(busy_donors)

    donor_usage = {}
    results = []

    # Step 2: Score requests
    requests["priority_score"] = requests.apply(
        compute_priority_score, axis=1
    )

    # print("\nDEBUG PRIORITY SCORES\n")

    # print(requests[[
        #"request_id",
        #"urgency_level",
        #"hours_since_posted",
        #"priority_score"
    # ]].head(15))

    
    # Step 3: Filter active requests
    active_requests = requests[requests["status"] == "Active"].copy()
    active_requests = active_requests.sort_values(
        by="priority_score", ascending=False
    )

    # Step 4: Match donors
    for _, request in active_requests.iterrows():

        matched_donors = match_donors_to_request(
            request, donors, donor_usage
        )

        results.append({
            "request_id": request["request_id"],
            "priority_score": request["priority_score"],
            "matched_donors": matched_donors
        })

    return pd.DataFrame(results)