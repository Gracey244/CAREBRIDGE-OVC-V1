# CareBridge OVC Matching Engine V1

The CareBridge OVC Matching Engine V1 is a rules-based system that prioritizes orphanage needs and matches them with the most relevant donors.

It ensures that urgent and high-impact requests are addressed first, while fairly distributing opportunities across available donors.


##  What the System Does

1. Takes in active requests (needs from orphanages)
2. Scores each request based on urgency and context
3. Matches each request with suitable donors
4. Ranks donors based on relevance and fairness
5. Outputs a list of best-fit donors per request

## Output

Each request returns:

- priority_score
- List of matched donors


##  How Matching Works

### 1. Priority Scoring

Each request is assigned a priority score (0–100) based on:

* Urgency level (High, Medium, Low)
* Time since request was posted
* Facility fulfillment history
* Request duplication status
* Category


### 2. Donor Filtering

Donors are filtered based on:

* Preferred category
* Need type (Cash / Goods / Either)
* Location (Lagos or Ibadan for V1)
* Availability (not already handling another request)


### 3. Ranking System

Matched donors are ranked using:

* Donation history (more active donors rank higher)
* Recency of last donation
* Usage penalty (to prevent overuse of same donors)
* Small randomness (to avoid bias and improve fairness)


### 4. Fairness Control

To prevent donor fatigue:

* Each donor has a reuse cap
* Overused donors are skipped during matching


### 5. Fallback Matching

If strict matching yields too few donors:

* The system relaxes constraints (e.g., location/type)
* Ensures every request still gets potential matches


##  Key Improvements in V1

###  Fairness

* Donor reuse is limited to avoid overloading a few donors

###  Fallback Logic

* Prevents situations where requests receive no matches

###  Ranking System

* Combines multiple signals to produce high-quality matches

###  Reproducibility

* Random seed ensures consistent results across environments


##  Assumptions

* All data (requests, donors, donations) is clean and valid
* Donors have defined preferences (category, type, location)
* Only "Active" requests are processed
* Location is limited to Lagos and Ibadan (V1 scope)


##  Limitations

* No real-time updates (batch processing only)
* No machine learning (rules-based system)
* No geographic distance calculation (strict location match)
* No donor response tracking (handled by backend)
* Matching does not guarantee fulfillment (only recommendation)


##  How to Run the System

### 1. Install dependencies

```bash
pip install -r requirements.txt
```


### 2. Ensure data files are present

* requests.csv
* donors.csv
* donations.csv


### 3. Run the engine

```bash
python main.py
```


### 4. Output

* Results will be printed in the terminal
* Saved as: `matching_results.csv`


##  Future Improvements (V2)

* Machine learning-based ranking
* Location distance scoring (geo-based)
* Donor response prediction
* Real-time API integration


##  Summary

This system provides a scalable foundation for intelligent donor-request matching by combining prioritization, fairness, and fallback strategies — ensuring that no critical need is left unattended.
