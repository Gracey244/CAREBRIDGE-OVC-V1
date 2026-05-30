"""
CareBridge OVC Matching Engine — REST API
Deploy with: uvicorn api:app --host 0.0.0.0 --port 8000
"""

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
    Each record mirrors a row in the corresponding CSV.

    Example payload:
    {
      "requests": [
        {
          "request_id": "R001",
          "facility_id": "F001",
          "category": "Food",
          "need_type": "Cash",
          "request_text": "We need food supplies",
          "items": "Rice, Beans",
          "quantity": 20, 10, 
          "urgency_level": "High",
          "children_affected": 30,
          "location": "Lagos",
          "date_submitted": "2026-05-01",
          "hours_since_posted": 5,
          "facility_fulfilment_rate": 0.6,
          "is_duplicate": false,
          "status": "Active",
          "cash_equivalent": 50000,
          "priority_score": 90
        }
      ],
      "donors": [
        {
          "donor_id": "D001",
          "donor_name": "John Doe",
          "preferred_category": "Food",
          "preferred_type": "Cash",
          "location": "Lagos",
          "budget": 100000,
          "donation_count": 10,
          "last_donation_days": 3
        }
      ],
      "donations": [
        {
          "donation_id": "DN001",
          "request_id": "R001",
          "donor_id": "D001",
          "amount": 50000,
          "status": "Pending",
          "date": "2026-05-01"
        }
      ]
    }
    """
    requests: List[Dict[str, Any]]
    donors: List[Dict[str, Any]]
    donations: List[Dict[str, Any]]


class MatchResult(BaseModel):
    request_id: str
    priority_score: float
    matched_donors: List[Any]   # engine may return dicts or ids


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
    busy_donors: int         # donors with a Pending donation
    available_donors: int    # donors free to be matched
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
        requests_df  = pd.DataFrame(payload.requests)
        donors_df    = pd.DataFrame(payload.donors)
        donations_df = pd.DataFrame(payload.donations)

        # Validate minimum required columns using your actual CSV column names
        _validate_columns(
            requests_df,
            ["request_id", "status", "urgency_level", "hours_since_posted",
             "facility_fulfilment_rate", "is_duplicate", "category", "need_type"],
            "requests"
        )
        _validate_columns(
            donors_df,
            ["donor_id", "preferred_category", "preferred_type",
             "location", "donation_count", "last_donation_days"],
            "donors"
        )
        _validate_columns(
            donations_df,
            ["donor_id", "status"],
            "donations"
        )

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
        requests_df  = pd.DataFrame(payload.requests)
        donors_df    = pd.DataFrame(payload.donors)
        donations_df = pd.DataFrame(payload.donations)

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
    Useful for frontend dashboard counters without running the full engine.

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

        # Donor availability — mirrors engine logic exactly
        busy_donor_ids   = set(donations_df[donations_df["status"] == "Pending"]["donor_id"])
        busy_donors      = int(donors_df["donor_id"].isin(busy_donor_ids).sum())
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