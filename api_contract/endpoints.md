# CareBridge OVC Matching Engine — API Contract

Base URL: https://carebridge-ovc-v1.onrender.com


All endpoints accept and return JSON.  
All `POST` endpoints expect the same request body structure.


## Request Body (shared across all POST endpoints)

```json
{
  "requests": [
    {
      "request_id": "R001",
      "facility_id": "F001",
      "category": "Food",
      "urgency_level": "High",
      "status": "Active",
      "hours_since_posted": 5,
      "is_duplicate": false,
      "fulfillment_rate": 0.6
    }
  ],
  "donors": [
    {
      "donor_id": "D001",
      "preferred_category": "Food",
      "need_type": "Either",
      "location": "Lagos",
      "total_donations": 10,
      "last_donation_days_ago": 3
    }
  ],
  "donations": [
    {
      "donation_id": "DON001",
      "donor_id": "D001",
      "request_id": "R001",
      "status": "Pending"
    }
  ]
}
```


## Endpoints


### GET `/health`

Confirms the service is live. Call this first to check the API is up.

**Request:** No body required.

**Response `200 OK`:**
```json
{
  "status": "ok",
  "service": "CareBridge OVC Matching Engine"
}
```


### POST `/match`

Runs the full matching engine. Returns a ranked list of matched donors
for every active request, ordered by priority score (highest first).

**Request body:** See shared structure above.

**Response `200 OK`:**
```json
{
  "status": "success",
  "total_requests_processed": 2,
  "results": [
    {
      "request_id": "R001",
      "priority_score": 87.5,
      "matched_donors": ["D001", "D004"]
    },
    {
      "request_id": "R002",
      "priority_score": 42.0,
      "matched_donors": ["D002"]
    }
  ]
}
```

**Error responses:**

| Code | Meaning |
|------|---------|
| `422` | Missing a required column in the data you sent |
| `500` | Internal engine error — check your data format |


### POST `/match/single-request?request_id=R001`

Re-runs matching for **one specific request only**.  
Useful after a donor declines — no need to re-run the full engine.

**Query parameter:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `request_id` | string | ✅ Yes | The ID of the request to rematch |

**Request body:** See shared structure above.

**Response `200 OK`:**
```json
{
  "status": "success",
  "request_id": "R001",
  "priority_score": 87.5,
  "matched_donors": ["D001", "D004"]
}
```

**Response when no donors match:**
```json
{
  "status": "no_matches",
  "request_id": "R001",
  "matched_donors": []
}
```

**Error responses:**

| Code | Meaning |
|------|---------|
| `404` | `request_id` not found in the data you sent |
| `500` | Internal engine error |


### POST `/stats`

Returns a summary of the data sent — useful for dashboard counters.  
Does **not** run the matching engine, so it's fast.

**Request body:** See shared structure above.

**Response `200 OK`:**
```json
{
  "total_requests": 120,
  "total_donors": 45,
  "total_donations": 300,
  "active_requests": 18,
  "inactive_requests": 102,
  "busy_donors": 10,
  "available_donors": 35,
  "pending_donations": 12,
  "completed_donations": 288
}
```


## Notes for the Backend Team

- **No authentication** is required during hackathon development.
- The AI engine does **not store any data** — send your data on every request.
- A donor is considered **busy** if they have a donation with `status: "Pending"`.
- Only requests with `status: "Active"` are processed by `/match`.
- Interactive docs (auto-generated) are available at:  
  `https://carebridge-ovc-v1.onrender.com/docs`