import numpy as np
from config.config import *

# Ensure reproducibility
np.random.seed(RANDOM_SEED)

# MATCHING FUNCTION

def match_donors_to_request(request, donors_df, donor_usage, top_n=TOP_N):

    matched = donors_df.copy()

    # Step 1: Strict filtering
    strict_matches = matched[
        (matched["preferred_category"] == request["category"]) &
        (matched["location"] == request["location"]) &
        (
            (matched["preferred_type"] == request["need_type"]) |
            (matched["preferred_type"] == "Either")
        ) &
        (matched["is_available"] == True)
    ]

    # Step 2: Fallback if needed
    if ENABLE_FALLBACK and len(strict_matches) < 5:
        fallback_matches = matched[
            (matched["preferred_category"] == request["category"]) &
            (matched["is_available"] == True)
        ]
        matched = fallback_matches
    else:
        matched = strict_matches

    if matched.empty:
        return []

    matched = matched.copy()

    # Step 3: Usage penalty
    matched["usage_penalty"] = matched["donor_id"].map(
        lambda x: donor_usage.get(x, 0) * USAGE_PENALTY_WEIGHT
    )

    # Step 4: Ranking score
    matched["rank_score"] = (
        matched["donation_count"] * 1.5
        - matched["last_donation_days"] * 0.5
        - matched["usage_penalty"]
    )

    # Step 5: Add randomness for fairness
    matched["rank_score"] += np.random.uniform(
        RANDOMNESS_MIN,
        RANDOMNESS_MAX,
        size=len(matched)
    )

    # Step 5b: Prevent negative ranking scores
    matched["rank_score"] = matched["rank_score"].clip(lower=0)

    # Step 6: Sort donors by highest ranking score
    matched = matched.sort_values(by="rank_score", ascending=False)

    # Step 7: Select donors with cap + refill logic
    donor_list = []

    for _, donor in matched.iterrows():

        donor_id = donor["donor_id"]

        # Skip overused donors
        if donor_usage.get(donor_id, 0) > MAX_DONOR_REUSE:
            continue

        donor_list.append({
            "donor_id": donor_id,
            "donor_name": donor["donor_name"],
            "rank_score": donor["rank_score"]
        })

        # Track usage
        donor_usage[donor_id] = donor_usage.get(donor_id, 0) + 1

        # Stop when we reach top_n AFTER filtering
        if len(donor_list) >= top_n:
            break

    return donor_list