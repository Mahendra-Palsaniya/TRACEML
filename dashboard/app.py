"""TRACE Streamlit dashboard. Displays actual API results; never simulates live traffic."""
import io
import os

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("TRACE_API_URL", "http://localhost:8000").rstrip("/")
st.set_page_config(page_title="TRACE Intrusion Detection", layout="wide")
st.title("TRACE — Network Intrusion Detection")
st.caption("CSV analysis of network flows. This is not a live packet capture.")

with st.sidebar:
    api_url = st.text_input("Backend API URL", value=API_URL)
    timeout = st.number_input("Request timeout (seconds)", min_value=5, max_value=300, value=60)
    st.caption("Only connect to an API you trust. CSV data is sent to that endpoint.")

try:
    response = requests.get(f"{api_url.rstrip('/')}/health", timeout=10)
    response.raise_for_status()
    health = response.json()
    st.info(f"API: {health.get('status', 'unknown')} | Models: {health.get('models', {})}")
except (requests.RequestException, ValueError) as exc:
    st.error(f"Backend unavailable: {exc}")

uploaded = st.file_uploader("Upload a flow-feature CSV (up to 5 MiB / 1,000 rows)", type=["csv"])
if uploaded is not None:
    raw = uploaded.getvalue()
    if len(raw) > 5 * 1024 * 1024:
        st.error("File exceeds the backend's 5 MiB limit.")
    else:
        try:
            preview = pd.read_csv(io.BytesIO(raw), nrows=5)
            st.subheader("Input preview")
            st.dataframe(preview, use_container_width=True)
        except Exception as exc:
            st.error(f"Cannot preview CSV: {exc}")
        if st.button("Analyze CSV", type="primary"):
            try:
                with st.spinner("Analyzing with the TRACE backend..."):
                    res = requests.post(
                        f"{api_url.rstrip('/')}/analyze-csv",
                        files={"file": (uploaded.name, raw, "text/csv")},
                        timeout=int(timeout),
                    )
                if not res.ok:
                    try:
                        detail = res.json().get("detail", res.text)
                    except ValueError:
                        detail = res.text
                    st.error(f"Analysis rejected (HTTP {res.status_code}): {detail}")
                else:
                    payload = res.json()
                    rows = payload.get("results", [])
                    if not rows:
                        st.warning("The backend returned no results.")
                    else:
                        table = pd.DataFrame(rows)
                        total, anomalies = len(table), int(table["is_anomaly"].sum())
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Flows", total)
                        c2.metric("Anomalies", anomalies)
                        c3.metric("Normal", total - anomalies)
                        show = table.copy()
                        show.insert(0, "flow_number", range(1, len(show) + 1))
                        if "is_anomaly" in show:
                            selection = st.selectbox("Filter", ["All", "Anomalies", "Normal"])
                            if selection == "Anomalies":
                                show = show[show["is_anomaly"]]
                            elif selection == "Normal":
                                show = show[~show["is_anomaly"]]
                        st.dataframe(show, use_container_width=True)
                        st.download_button(
                            "Download results CSV",
                            table.to_csv(index=False).encode("utf-8"),
                            file_name="trace_results.csv",
                            mime="text/csv",
                        )
                        if "attack_type" in table:
                            st.subheader("Attack classes")
                            st.bar_chart(table["attack_type"].value_counts())
                        st.caption("Results are model outputs, not independently verified ground truth.")
            except (requests.RequestException, ValueError, KeyError) as exc:
                st.error(f"Analysis failed: {exc}")
