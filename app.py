"""
CareBridge OVC Matching Engine — REST API
Deploy with: uvicorn api:app --host 0.0.0.0 --port 8000
"""

import io
import traceback
from typing import Any, Dict, List

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.engine import run_matching_engine

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="CareBridge OVC Matching Engine",
    description="Matches orphanage requests to the most relevant donors.",
    version="1.0.0",
)

# Allow all origins so the backend team can call this freely during development.
# Tighten this to specific domains before going to production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class MatchRequest(BaseModel):
    """
    The backend sends three lists of records — one per data source.
    Each record is a plain dict that mirrors a row in the corresponding CSV.

    Example payload:
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
    """
    requests: List[Dict[str, Any]]
    donors: List[Dict[str, Any]]
    donations: List[Dict[str, Any]]


class MatchedDonor(BaseModel):
    donor_id: str
    rank: int


class MatchResult(BaseModel):
    request_id: str
    priority_score: float
    matched_donors: List[Any]  # keeps flexibility — engine may return dicts or ids


class MatchResponse(BaseModel):
    status: str
    total_requests_processed: int
    results: List[MatchResult]


class StatsResponse(BaseModel):
    total_requests: int
    total_donors: int
    total_donations: int
    active_requests: int
    inactive_requests: int
    busy_donors: int        # donors with a pending donation
    available_donors: int   # donors free to be matched
    pending_donations: int
    completed_donations: int


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
def health_check():
    """Quick liveness check — call this to confirm the service is running."""
    return {"status": "ok", "service": "CareBridge OVC Matching Engine"}


@app.post("/match", response_model=MatchResponse, tags=["Matching"])
def match_donors(payload: MatchRequest):
    """
    Run the matching engine on the provided data.

    - Accepts requests, donors, and donations as JSON arrays.
    - Returns a ranked list of matched donors for each active request.
    - Requests are returned in descending priority order.
    """
    try:
        # Convert incoming JSON to DataFrames (same format the engine expects)
        requests_df = pd.DataFrame(payload.requests)
        donors_df = pd.DataFrame(payload.donors)
        donations_df = pd.DataFrame(payload.donations)

        # Validate that the minimum required columns exist
        _validate_columns(requests_df, ["request_id", "status"], "requests")
        _validate_columns(donors_df, ["donor_id"], "donors")
        _validate_columns(donations_df, ["donor_id", "status"], "donations")

        # Run the engine
        results_df = run_matching_engine(requests_df, donors_df, donations_df)

        # Serialize output
        results = []
        for _, row in results_df.iterrows():
            results.append(
                MatchResult(
                    request_id=str(row["request_id"]),
                    priority_score=round(float(row["priority_score"]), 4),
                    matched_donors=row["matched_donors"],
                )
            )

        return MatchResponse(
            status="success",
            total_requests_processed=len(results),
            results=results,
        )

    except KeyError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Missing expected column in input data: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Matching engine error: {str(e)}\n{traceback.format_exc()}",
        )


@app.post("/match/single-request", tags=["Matching"])
def match_single_request(payload: MatchRequest, request_id: str):
    """
    Run matching for one specific request_id only.
    Useful for the backend to re-run matching after a donor declines.
    """
    try:
        requests_df = pd.DataFrame(payload.requests)
        donors_df = pd.DataFrame(payload.donors)
        donations_df = pd.DataFrame(payload.donations)

        # Filter to the single request
        filtered = requests_df[requests_df["request_id"] == request_id]
        if filtered.empty:
            raise HTTPException(
                status_code=404,
                detail=f"request_id '{request_id}' not found in the provided data.",
            )

        results_df = run_matching_engine(filtered, donors_df, donations_df)

        if results_df.empty:
            return {"status": "no_matches", "request_id": request_id, "matched_donors": []}

        row = results_df.iloc[0]
        return {
            "status": "success",
            "request_id": str(row["request_id"]),
            "priority_score": round(float(row["priority_score"]), 4),
            "matched_donors": row["matched_donors"],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stats", response_model=StatsResponse, tags=["Stats"])
def get_stats(payload: MatchRequest):
    """
    Returns a summary of the data sent in the request body.

    Useful for the frontend dashboard to display live counts
    without running the full matching engine.

    Example response:
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
    """
    try:
        requests_df  = pd.DataFrame(payload.requests)
        donors_df    = pd.DataFrame(payload.donors)
        donations_df = pd.DataFrame(payload.donations)

        _validate_columns(requests_df,  ["request_id", "status"], "requests")
        _validate_columns(donors_df,    ["donor_id"],              "donors")
        _validate_columns(donations_df, ["donor_id", "status"],    "donations")

        # Requests breakdown
        active_requests   = int((requests_df["status"] == "Active").sum())
        inactive_requests = int((requests_df["status"] != "Active").sum())

        # Donations breakdown
        pending_donations   = int((donations_df["status"] == "Pending").sum())
        completed_donations = int((donations_df["status"] == "Completed").sum())

        # Donor availability (mirrors engine logic — busy = has a pending donation)
        busy_donor_ids  = set(donations_df[donations_df["status"] == "Pending"]["donor_id"])
        busy_donors     = int(donors_df["donor_id"].isin(busy_donor_ids).sum())
        available_donors = len(donors_df) - busy_donors

        return StatsResponse(
            total_requests      = len(requests_df),
            total_donors        = len(donors_df),
            total_donations     = len(donations_df),
            active_requests     = active_requests,
            inactive_requests   = inactive_requests,
            busy_donors         = busy_donors,
            available_donors    = available_donors,
            pending_donations   = pending_donations,
            completed_donations = completed_donations,
        )

    except KeyError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Missing expected column in input data: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Stats error: {str(e)}\n{traceback.format_exc()}",
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _validate_columns(df: pd.DataFrame, required: List[str], label: str):
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise KeyError(f"'{label}' data is missing columns: {missing}")