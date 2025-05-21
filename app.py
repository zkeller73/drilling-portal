import streamlit as st
import pandas as pd
from datetime import date
import os
import json
import base64

UPLOAD_FOLDER = "/mnt/data/uploaded_reports"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

REPORT_LOG = "report_log.csv"
ESTIMATE_FILE = "estimates.json"

# --- Sidebar Navigation ---
st.sidebar.title("📁 Navigation")
page = st.sidebar.radio("Go to", ["Inputs", "View Reports"])

# === INPUTS PAGE ===
if page == "Inputs":
    st.title("🔐 Secure Input Portal")

    # Password protection
    password = st.text_input("Enter password to continue", type="password")
    if password != "oilmoney":
        st.warning("Incorrect password.")
        st.stop()

    # (Upload form, AFE form, and delete logic continues here…)

# === VIEW REPORTS PAGE ===
elif page == "View Reports":
    st.title("📊 Drilling Report Log & Cost Tracking")

    if os.path.exists(REPORT_LOG):
        df = pd.read_csv(REPORT_LOG)

        # Check required columns
        required_cols = {"Day #", "Daily Cost", "Phase", "Filename", "Date"}
        if required_cols.issubset(df.columns):
            df["Daily Cost"] = pd.to_numeric(df["Daily Cost"], errors="coerce")
            df["Day #"] = pd.to_numeric(df["Day #"], errors="coerce")
            df = df.dropna(subset=["Day #", "Daily Cost"])
            st.dataframe(df)

            st.subheader("💰 Daily Cost vs Drilling Day")
            if not df.empty:
                st.line_chart(df[["Day #", "Daily Cost"]].set_index("Day #"))

            # Cost summary
            if os.path.exists(ESTIMATE_FILE):
                with open(ESTIMATE_FILE, "r") as f:
                    estimates = json.load(f)

                drilling_afe = estimates.get("Drilling AFE", 0)
                completion_afe = estimates.get("Completion AFE", 0)
                drilling_actual = df[df["Phase"] == "Drilling"]["Daily Cost"].sum()
                completion_actual = df[df["Phase"] == "Completion"]["Daily Cost"].sum()

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### 🛢️ Drilling Cost Summary")
                    st.markdown(f"**AFE:** ${drilling_afe:,.0f}")
                    st.markdown(f"**Actual:** ${drilling_actual:,.0f}")
                    st.markdown(f"**Variance:** ${drilling_actual - drilling_afe:,.0f}")
                with col2:
                    st.markdown("### 🔧 Completion Cost Summary")
                    st.markdown(f"**AFE:** ${completion_afe:,.0f}")
                    st.markdown(f"**Actual:** ${completion_actual:,.0f}")
                    st.markdown(f"**Variance:** ${completion_actual - completion_afe:,.0f}")

            # PDF Viewer
            st.subheader("📄 View Uploaded PDF")
            if "Filename" in df.columns and not df["Filename"].isna().all():
                selected_file = st.selectbox("Select a report to view:", df["Filename"].unique())

                if selected_file:
                    pdf_path = os.path.join(UPLOAD_FOLDER, selected_file)
                    if os.path.exists(pdf_path):
                        with open(pdf_path, "rb") as f:
                            base64_pdf = base64.b64encode(f.read()).decode("utf-8")
                            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800px" type="application/pdf"></iframe>'
                            st.markdown(pdf_display, unsafe_allow_html=True)
        else:
            st.error("Missing columns in report log.")
    else:
        st.warning("No reports uploaded yet.")
