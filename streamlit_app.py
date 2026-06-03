"""
CareBridge OVC Matching Engine — Streamlit Demo App
Run locally:  streamlit run streamlit_app.py
"""

import io
import json

import pandas as pd
import streamlit as st

from src.engine import run_matching_engine

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CareBridge OVC Matching Engine",
    page_icon="🤝",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🤝 CareBridge OVC Matching Engine")
st.markdown(
    "Upload your data files below to run the matching engine and see ranked donor matches "
    "for each active orphanage request."
)
st.divider()

# ---------------------------------------------------------------------------
# Sidebar — data source toggle
# ---------------------------------------------------------------------------
st.sidebar.header("⚙️ Settings")
data_source = st.sidebar.radio(
    "Data source",
    ["Upload CSV files", "Use sample data"],
    index=1,
)

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
requests_df = donors_df = donations_df = None

if data_source == "Upload CSV files":
    st.subheader("📂 Upload your data files")
    col1, col2, col3 = st.columns(3)

    with col1:
        req_file = st.file_uploader("requests.csv", type="csv")
        if req_file:
            requests_df = pd.read_csv(req_file)
            st.success(f"✅ {len(requests_df)} requests loaded")

    with col2:
        don_file = st.file_uploader("donors.csv", type="csv")
        if don_file:
            donors_df = pd.read_csv(don_file)
            st.success(f"✅ {len(donors_df)} donors loaded")

    with col3:
        dona_file = st.file_uploader("donations.csv", type="csv")
        if dona_file:
            donations_df = pd.read_csv(dona_file)
            st.success(f"✅ {len(donations_df)} donations loaded")

else:
    # ── Sample data matching exact column names from your real CSVs ──────────
    requests_df = pd.DataFrame([
        {
            "request_id": "R001", "facility_id": "F001", "category": "Food",
            "need_type": "Kind", "request_text": "Urgently need food supplies",
            "items": "Rice, Beans, Oil", "quantity": "50, 30, 20",
            "urgency_level": "High", "children_affected": 60,
            "location": "Lagos", "date_submitted": "2026-03-18",
            "hours_since_posted": 30, "facility_fulfilment_rate": 0.85,
            "is_duplicate": False, "status": "Active",
            "cash_equivalent": 50000, "priority_score": 90,
        },
        {
            "request_id": "R002", "facility_id": "F002", "category": "Medical",
            "need_type": "Cash", "request_text": "Need medical supplies urgently",
            "items": "Drugs, Bandages", "quantity": "10, 50",
            "urgency_level": "Medium", "children_affected": 20,
            "location": "Abuja", "date_submitted": "2026-03-19",
            "hours_since_posted": 10, "facility_fulfilment_rate": 0.60,
            "is_duplicate": False, "status": "Active",
            "cash_equivalent": 30000, "priority_score": 0,
        },
        {
            "request_id": "R003", "facility_id": "F001", "category": "Education",
            "need_type": "Kind", "request_text": "Need school supplies",
            "items": "Books, Pens", "quantity": "100, 200",
            "urgency_level": "Low", "children_affected": 40,
            "location": "Lagos", "date_submitted": "2026-03-20",
            "hours_since_posted": 48, "facility_fulfilment_rate": 0.90,
            "is_duplicate": True, "status": "Active",
            "cash_equivalent": 20000, "priority_score": 0,
        },
        {
            "request_id": "R004", "facility_id": "F003", "category": "Food",
            "need_type": "Cash", "request_text": "Need cash for food procurement",
            "items": "Rice", "quantity": "100",
            "urgency_level": "High", "children_affected": 80,
            "location": "Kano", "date_submitted": "2026-03-21",
            "hours_since_posted": 1, "facility_fulfilment_rate": 0.20,
            "is_duplicate": False, "status": "Inactive",
            "cash_equivalent": 80000, "priority_score": 0,
        },
    ])

    donors_df = pd.DataFrame([
        {
            "donor_id": "D001", "donor_name": "Helping Hands Foundation",
            "preferred_category": "Food", "preferred_type": "Kind",
            "location": "Lagos", "budget": 60000,
            "donation_count": 25, "last_donation_days": 3,
        },
        {
            "donor_id": "D002", "donor_name": "Care Foundation",
            "preferred_category": "Medical", "preferred_type": "Cash",
            "location": "Abuja", "budget": 40000,
            "donation_count": 10, "last_donation_days": 7,
        },
        {
            "donor_id": "D003", "donor_name": "Education First NGO",
            "preferred_category": "Education", "preferred_type": "Kind",
            "location": "Lagos", "budget": 25000,
            "donation_count": 15, "last_donation_days": 1,
        },
        {
            "donor_id": "D004", "donor_name": "Food for All",
            "preferred_category": "Food", "preferred_type": "Cash",
            "location": "Kano", "budget": 90000,
            "donation_count": 5, "last_donation_days": 14,
        },
    ])

    donations_df = pd.DataFrame([
        {
            "donation_id": "DN001", "request_id": "R002", "donor_id": "D002",
            "amount": 30000, "status": "Pending", "date": "2026-03-15",
        },
        {
            "donation_id": "DN002", "request_id": "R001", "donor_id": "D001",
            "amount": 50000, "status": "Completed", "date": "2026-03-10",
        },
    ])

    st.info("ℹ️ Using built-in sample data. Switch to **Upload CSV files** in the sidebar to use your own.")

st.divider()

# ---------------------------------------------------------------------------
# Preview loaded data (collapsible)
# ---------------------------------------------------------------------------
if requests_df is not None and donors_df is not None and donations_df is not None:
    with st.expander("🔍 Preview loaded data", expanded=False):
        t1, t2, t3 = st.tabs(["Requests", "Donors", "Donations"])
        with t1:
            st.dataframe(requests_df, use_container_width=True)
        with t2:
            st.dataframe(donors_df, use_container_width=True)
        with t3:
            st.dataframe(donations_df, use_container_width=True)

    st.divider()

    # -----------------------------------------------------------------------
    # Run engine
    # -----------------------------------------------------------------------
    st.subheader("🚀 Run Matching Engine")

    if st.button("▶️ Run Matching", type="primary", use_container_width=True):
        with st.spinner("Running matching engine…"):
            try:
                results_df = run_matching_engine(
                    requests_df.copy(),
                    donors_df.copy(),
                    donations_df.copy(),
                )

                st.success(
                    f"✅ Matching complete — {len(results_df)} active request(s) processed."
                )
                st.divider()

                # ── Summary metrics ──────────────────────────────────────
                st.subheader("📊 Summary")
                m1, m2, m3 = st.columns(3)
                m1.metric("Active Requests Processed", len(results_df))
                m2.metric(
                    "Avg Priority Score",
                    f"{results_df['priority_score'].mean():.1f}" if not results_df.empty else "—",
                )
                total_matches = results_df["matched_donors"].apply(
                    lambda x: len(x) if isinstance(x, list) else 0
                ).sum()
                m3.metric("Total Donor Matches", total_matches)

                st.divider()

                # ── Per-request results ───────────────────────────────────
                st.subheader("📋 Results by Request")

                for _, row in results_df.iterrows():
                    matched = row["matched_donors"]
                    match_count = len(matched) if isinstance(matched, list) else 0
                    score = round(float(row["priority_score"]), 1)

                    # Colour-code priority badge
                    if score >= 70:
                        badge = "🔴 High Priority"
                    elif score >= 40:
                        badge = "🟡 Medium Priority"
                    else:
                        badge = "🟢 Low Priority"

                    with st.expander(
                        f"{badge} | Request {row['request_id']}  —  Score: {score}  —  {match_count} donor(s) matched",
                        expanded=(score >= 70),
                    ):
                        col_a, col_b = st.columns([1, 2])
                        with col_a:
                            st.metric("Priority Score", score)
                            st.metric("Matched Donors", match_count)

                        with col_b:
                            if match_count == 0:
                                st.warning("No donors matched for this request.")
                            elif isinstance(matched[0], dict):
                                st.dataframe(pd.DataFrame(matched), use_container_width=True)
                            else:
                                st.write("**Matched donor IDs (ranked):**")
                                for i, d in enumerate(matched, 1):
                                    st.write(f"{i}. `{d}`")

                st.divider()

                # ── Full results table ────────────────────────────────────
                st.subheader("📥 Full Results Table")
                display_df = results_df[["request_id", "priority_score"]].copy()
                display_df["matched_donors"] = results_df["matched_donors"].apply(
                    lambda x: json.dumps(x) if isinstance(x, list) else str(x)
                )
                st.dataframe(display_df, use_container_width=True)

                # ── Download button ───────────────────────────────────────
                csv_buffer = io.StringIO()
                display_df.to_csv(csv_buffer, index=False)
                st.download_button(
                    label="⬇️ Download results as CSV",
                    data=csv_buffer.getvalue(),
                    file_name="matching_results.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            except Exception as e:
                st.error(f"❌ Engine error: {e}")
                st.exception(e)

else:
    st.warning("⚠️ Please upload all three CSV files (or switch to sample data) to continue.")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.divider()
st.caption("CareBridge OVC Matching Engine v1 · Built for hackathon demo purposes")