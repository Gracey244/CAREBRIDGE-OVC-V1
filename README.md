# CareBridge OVC Matching Engine V1

The CareBridge OVC Matching Engine V1 is a rules-based system that prioritizes orphanage needs and matches them with the most relevant donors.

It ensures that urgent and high-impact requests are addressed first, while fairly distributing opportunities across available donors.



## 🔗 Live Deployments

| Service | URL | Purpose |
|---|---|---|
| 🚀 REST API |  https://carebridge-ovc-v1.onrender.com | Backend integration |
| 📊 Demo App | https://carebridge-ovc-v1-e2jqgsmpmrvqg8y7jrkkss.streamlit.app/ | Visual demo for judges |
| 📖 API Docs | https://carebridge-ovc-v1.onrender.com/docs | Interactive endpoint testing |
| 📋 API Contract | [api_contract/endpoints.md](./api_contract/endpoints.md) | Integration guide for backend team |



## What the System Does

1. Takes in active requests (needs from orphanages)
2. Scores each request based on urgency and context
3. Matches each request with suitable donors
4. Ranks donors based on relevance and fairness
5. Outputs a list of best-fit donors per request

## Output

Each request returns:

- priority_score
- List of matched donors


## How Matching Works

### 1. Priority Scoring

Each request is assigned a priority score (0–100) based on:

- Urgency level (High, Medium, Low)
- Time since request was posted
- Facility fulfillment history
- Request duplication status
- Category

### 2. Donor Filtering

Donors are filtered based on:

- Preferred category
- Need type (Cash / Goods / Either)
- Location (Lagos or Ibadan for V1)
- Availability (not already handling another request)

### 3. Ranking System

Matched donors are ranked using:

- Donation history (more active donors rank higher)
- Recency of last donation
- Usage penalty (to prevent overuse of same donors)
- Small randomness (to avoid bias and improve fairness)

### 4. Fairness Control

To prevent donor fatigue:

- Each donor has a reuse cap
- Overused donors are skipped during matching

### 5. Fallback Matching

If strict matching yields too few donors:

- The system relaxes constraints (e.g., location/type)
- Ensures every request still gets potential matches


## Key Improvements in V1

### Fairness
- Donor reuse is limited to avoid overloading a few donors

### Fallback Logic
- Prevents situations where requests receive no matches

### Ranking System
- Combines multiple signals to produce high-quality matches

### Reproducibility
- Random seed ensures consistent results across environments


## Assumptions

- All data (requests, donors, donations) is clean and valid
- Donors have defined preferences (category, type, location)
- Only "Active" requests are processed
- Location is limited to Lagos and Ibadan (V1 scope)

## Limitations

- No real-time updates (batch processing only)
- No machine learning (rules-based system)
- No geographic distance calculation (strict location match)
- No donor response tracking (handled by backend)
- Matching does not guarantee fulfillment (only recommendation)


## How to Run the System

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Ensure data files are present in `data_samples/`

- requests.csv
- donors.csv
- donations.csv

### 3. Run the engine locally

```bash
python main.py
```

### 4. Run the REST API locally

```bash
uvicorn app:app --reload
```

Then visit `http://localhost:8000/docs` to test all endpoints interactively.

### 5. Run the Streamlit demo locally

```bash
streamlit run streamlit_app.py
```

### 6. Output

- Results printed in terminal
- Saved as: `matching_results.csv`


## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check if API is live |
| POST | `/match` | Run full matching engine |
| POST | `/match/single-request?request_id=R001` | Rematch one specific request |
| POST | `/stats` | Get summary counts without running engine |

Full request/response examples → [api_contract/endpoints.md](./api_contract/endpoints.md)


## Project Structure

```
CAREBRIDGE-OVC-V1/
├── api.py                    # FastAPI REST API (backend integration)
├── streamlit_app.py          # Streamlit demo app (presentation)
├── main.py                   # Local runner / entry point
├── requirements.txt          # Python dependencies
├── .streamlit/
│   └── config.toml           # Streamlit deployment config
├── api_contract/
│   └── endpoints.md          # API documentation for backend team
├── data_samples/
│   ├── requests.csv          # Sample orphanage requests
│   ├── donors.csv            # Sample donor data
│   └── donations.csv         # Sample donation history
└── src/
    ├── engine.py             # Main matching engine orchestrator
    ├── matching.py           # Donor matching logic
    └── scoring.py            # Request priority scoring logic
```


## Tech Stack

| Tool | Purpose |
|---|---|
| Python | Core language |
| Pandas | Data processing |
| FastAPI | REST API framework |
| Uvicorn | ASGI server |
| Streamlit | Demo/visualization app |
| Render | API deployment |
| Streamlit Cloud | Demo app deployment |


## Future Improvements (V2)

- Machine learning-based ranking
- Location distance scoring (geo-based)
- Donor response prediction
- Real-time API integration


## Summary

This system provides a scalable foundation for intelligent donor-request matching by combining prioritization, fairness, and fallback strategies — ensuring that no critical need is left unattended.