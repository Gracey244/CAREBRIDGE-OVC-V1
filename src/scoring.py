import pandas as pd
from config.config import *

# PRIORITY SCORING FUNCTION

def compute_priority_score(request):
    # print("SCORING:", request["request_id"]) (Debug)
    score = 0

    # Urgency scoring
    if request["urgency_level"] == "High":
        score += URGENCY_HIGH
    elif request["urgency_level"] == "Medium":
        score += URGENCY_MEDIUM
    else:
        score += URGENCY_LOW

    # Category bonus
    if request["category"] == "Medical":
        score += MEDICAL_BONUS

    # Time-based escalation
    if request["hours_since_posted"] > 24:
        score += OLD_REQUEST_24H
    elif request["hours_since_posted"] > 12:
        score += OLD_REQUEST_12H
    elif request["hours_since_posted"] > 6:
        score += OLD_REQUEST_6H 

    # Facility reliability
    if request["facility_fulfilment_rate"] > 0.8:
        score += HIGH_FULFILMENT_BONUS
    elif request["facility_fulfilment_rate"] < 0.5:
        score += LOW_FULFILMENT_PENALTY

    # Duplicate penalty
    if request["is_duplicate"]:
        score += DUPLICATE_PENALTY

    # Clamp between 0–100
    return max(0, min(100, score))