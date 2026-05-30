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
    # ── Minimal sample data so the app works out of the box ──────────────────
    requests_df = pd.DataFrame([
        {
            "request_id": "R001", "facility_id": "F001", "category": "Food",
            "urgency_level": "High", "status": "Active",
            "hours_since_posted": 2, "is_duplicate": False, "fulfillment_rate": 0.4,
        },
        {
            "request_id": "R002", "facility_id": "F002", "category": "Medical",
            "urgency_level": "Medium", "status": "Active",
            "hours_since_posted": 10, "is_duplicate": False, "fulfillment_rate": 0.7,
        },
        {
            "request_id": "R003", "facility_id": "F001", "category": "Education",
            "urgency_level": "Low", "status": "Active",
            "hours_since_posted": 48, "is_duplicate": True, "fulfillment_rate": 0.9,
        },
        {
            "request_id": "R004", "facility_id": "F003", "category": "Food",
            "urgency_level": "High", "status": "Inactive",
            "hours_since_posted": 1, "is_duplicate": False, "fulfillment_rate": 0.2,
        },
    ])

    donors_df = pd.DataFrame([
        {
            "donor_id": "D001", "preferred_category": "Food",
            "need_type": "Either", "location": "Lagos",
            "total_donations": 15, "last_donation_days_ago": 3,
        },
        {
            "donor_id": "D002", "preferred_category": "Medical",
            "need_type": "Cash", "location": "Ibadan",
            "total_donations": 8, "last_donation_days_ago": 7,
        },
        {
            "donor_id": "D003", "preferred_category": "Education",
            "need_type": "Goods", "location": "Lagos",
            "total_donations": 20, "last_donation_days_ago": 1,
        },
        {
            "donor_id": "D004", "preferred_category": "Food",
            "need_type": "Either", "location": "Ibadan",
            "total_donations": 5, "last_donation_days_ago": 14,
        },
    ])

    donations_df = pd.DataFrame([
        {"donation_id": "DON001", "donor_id": "D002", "request_id": "R002", "status": "Pending"},
        {"donation_id": "DON002", "donor_id": "D003", "request_id": "R001", "status": "Completed"},
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