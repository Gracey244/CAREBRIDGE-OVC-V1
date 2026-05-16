# CareBridge OVC Matching API Contract

##  Overview
This API defines how the backend system interacts with the CareBridge Matching Engine.

The matching engine:
- Receives a request (need)
- Returns prioritized donor matches

#  MATCH REQUEST ENDPOINT

## Endpoint
POST /api/match-request

##  Request Payload

{
  "request": {
    "request_id": "R001",
    "facility_id": "F001",
    "category": "Medical",
    "need_type": "Cash",
    "urgency_level": "High",
    "hours_since_posted": 30,
    "facility_fulfilment_rate": 0.75,
    "is_duplicate": false,
    "status": "Active",
    "location": "Ibadan",
    "cash_equivalent": 50000
  }
}

## Response Payload
{
  "request_id": "R001",
  "priority_score": 45,
  "matched_donors": [
    {
      "donor_id": "D007",
      "donor_name": "Global Relief,
      "rank_score": 42.5
    },
    {
      "donor_id": "D015",
      "donor_name": "Zenith Company",
      "rank_score": 38.2
    }
  ]
}

# BUSINESS LOGIC NOTES

- Only requests with status = "Active" are processed
- Priority score ranges from 0–100
- Maximum number of donors returned = configurable (default: 15)
- Donor reuse is limited to prevent fatigue
- Fallback matching ensures no request is left unmatched

# ERROR HANDLING

Example Error Response
{
  "error": "Invalid request data",
  "details": "Missing required field: category"
}

# STATUS FLOW (IMPORTANT)

Matching engine does NOT update request status.
Backend is responsible for:

- Sending match results to donors
- Handling donor commitment
- Updating request status: Active → Matched → Completed

# FUTURE EXTENSIONS (V2)
- ML-based ranking scores
- Real-time streaming matching
- Donor response prediction
- Geo-distance scoring