## CareBridge Prioritization & Matching Engine Integration Guide

This is a modular rules-based recommendation system/engine responsible for:

- Request prioritization
- Donor matching
- Donor ranking
- Fairness enforcement
- Availability filtering
- Fallback matching

The engine is designed to be invoked by the backend immediately after a facility request is created.

# System Architecture

Facility Request Submission
            ↓
Frontend API Call
            ↓
Backend Validation
            ↓
Database Save
            ↓
CALL MATCHING ENGINE  ← (Integration Point)
            ↓
Priority Scoring
            ↓
Donor Matching
            ↓
Ranked Match Results Returned
            ↓
Backend Stores Results
            ↓
Backend Sends Notifications
            ↓
First Donor Accepts
            ↓
Status Updates to "Matched"


# Responsibilities
AI/ML Engine handles:

- Request priority scoring
- Donor filtering
- Donor ranking
- Fairness logic
- Reuse prevention
- Availability checking
- Fallback matching

The backend handles:

- API routes
- Authentication
- Database persistence
- Notifications
- Real-time updates
- Request claiming
- Status transitions
- Concurrency management

## Integration Point
When To Call The Engine

The backend should invoke the engine:
✅ AFTER request validation
✅ BEFORE donor notifications

## Typical Backend Flow
# Step 1: Receive request from frontend
incoming_request = request.json

# Step 2: Validate payload
validate_request(incoming_request)

# Step 3: Save request to database
save_request(incoming_request)

# Step 4: Fetch active datasets
requests = fetch_active_requests()
donors = fetch_active_donors()
donations = fetch_active_donations()

# Step 5: Call matching engine
matches = run_matching_engine(
    requests,
    donors,
    donations
)

# Step 6: Save matching results
save_matches(matches)

# Step 7: Notify donors
notify_donors(matches)

## Engine Entry Point
Backend should import:

from src.engine import run_matching_engine

## Engine Function Signature
run_matching_engine(
    requests_df,
    donors_df,
    donations_df
)

## Expected Input DataFrames
# requests_df
Required columns:

request_id
facility_id
category
need_type
urgency_level
location
hours_since_posted
facility_fulfilment_rate
is_duplicate
status
cash_equivalent

# donors_df
Required columns:

donor_id
donor_name
preferred_category
preferred_type
location
budget
donation_count
last_donation_days

# donations_df
Required columns:

donation_id
donor_id
request_id
status

## Engine Output Format
Example output:

[
    {
        "request_id": "R001",
        "priority_score": 45,
        "matched_donors": [
            {
                "donor_id": "D007",
                "donor_name": "Global Relief Foundation",
                "rank_score": 72
            }
        ]
    }
]

## Matching Logic Summary
The engine prioritizes requests based on:

- urgency level
- request age
- category
- fulfillment rate
- duplicate detection
 
# Donor Matching Factors
Donors are filtered using:

- preferred category
- preferred need type
- location
- availability
- budget compatibility

# Ranking Factors
Donors are ranked using:

- historical donation activity
- recency of donation
- fairness penalty
- randomized tie-breaking

## Ranking Score Protection
To improve frontend readability and prevent confusing UI output,
ranking scores are clamped to a minimum of zero.
Example:

matched["rank_score"] = matched["rank_score"].clip(lower=0)

This ensures donors are never displayed with negative ranking scores.

# Fairness Logic
To prevent donor fatigue:

if donor_usage.get(donor_id, 0) > 3:
    continue

This prevents excessive reuse of the same donor.

# Fallback Matching
If strict matching fails:

- relaxed matching rules are applied
- broader donor candidates may be considered
This improves overall match rate.

# Availability Logic
Donors with pending donations are excluded:

busy_donors = set(active_donations["donor_id"])

# Status Handling
The engine reads:

Active
Matched
Completed
Pending

Backend remains responsible for status updates.

## Important Backend Notes
The engine does NOT:

- maintain sessions
- maintain memory
- manage transactions
It only computes recommendations.

# Request Claiming

The following PRD rule:

“First donor to commit claims the need”

should be implemented by backend/database logic.

The matching engine does not handle that.

## Production Migration
Current V1 uses CSV files for simulation.
Production should replace:

"pd.read_csv()"

with:
database queries
ORM calls
API payloads

## Error Handling Recommendations
Backend should validate:

- missing fields
- invalid statuses
- malformed requests
- empty donor pools
before invoking the engine.

## Recommended API Workflow
POST /requests
- Creates request.
- Triggers matching engine.
- Returns:

{
  "request_id": "R500",
  "priority_score": 45,
  "matched_donors": [...]
}
