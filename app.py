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

# --- Upload Page ---
elif page == "Upload Report":
    st.title("🔐 Secure Upload Area")

    # Simple password input
    password = st.text_input("Enter password to upload reports", type="password")

    if password != "oilmoney":
        st.warning("You must enter the correct password to access this page.")
        st.stop()

    # Upload form
    st.title("🛢️ Upload Daily Drilling Report")

    st.subheader("📋 Enter Metadata")
    report_date = st.date_input("Report Date", value=date.today())
    day_number = st.number_input("Drilling Day #", min_value=1)
    phase = st.selectbox("Phase", ["Drilling", "Completion"])
    daily_cost = st.number_input("Daily Cost ($)", min_value=0.0)
    depth = st.number_input("Depth (ft)", min_value=0)
    notes = st.text_area("Notes")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")

    if st.button("🚀 Submit Report"):
        if uploaded_file:
            filepath = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
            with open(filepath, "wb") as f:
                f.write(uploaded_file.getbuffer())

            new_data = {
                "Date": report_date.strftime("%Y-%m-%d"),
                "Day #": int(day_number),
                "Phase": phase,
                "Daily Cost": float(daily_cost),
                "Depth (ft)": int(depth),
                "Notes": notes,
                "Filename": uploaded_file.name,
            }

            if os.path.exists(REPORT_LOG):
                df = pd.read_csv(REPORT_LOG)
                df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
            else:
                df = pd.DataFrame([new_data])

            df.to_csv(REPORT_LOG, index=False)
            st.success("Report uploaded and saved.")
        else:
            st.warning("Please upload a PDF file.")

# --- Inputs Page ---
elif page == "Inputs":
    st.title("🔐 Secure Input Portal")

    # Password protection
    password = st.text_input("Enter password to continue", type="password")
    if password != "oilmoney":
        st.warning("Incorrect password.")
        st.stop()

    # === Upload Section ===
    st.subheader("🛢️ Upload Daily Drilling Report")

    report_date = st.date_input("Report Date", value=date.today())
    day_number = st.number_input("Drilling Day #", min_value=1)
    phase = st.selectbox("Phase", ["Drilling", "Completion"])
    daily_cost = st.number_input("Daily Cost ($)", min_value=0.0)
    depth = st.number_input("Depth (ft)", min_value=0)
    notes = st.text_area("Notes")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")

    if st.button("🚀 Submit Report"):
        if uploaded_file:
            filepath = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
            with open(filepath, "wb") as f:
                f.write(uploaded_file.getbuffer())

            new_data = {
                "Date": report_date.strftime("%Y-%m-%d"),
                "Day #": int(day_number),
                "Phase": phase,
                "Daily Cost": float(daily_cost),
                "Depth (ft)": int(depth),
                "Notes": notes,
                "Filename": uploaded_file.name,
            }

            if os.path.exists(REPORT_LOG):
                df = pd.read_csv(REPORT_LOG)
                df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
            else:
                df = pd.DataFrame([new_data])

            df.to_csv(REPORT_LOG, index=False)
            st.success("Report uploaded and saved.")
        else:
            st.warning("Please upload a PDF file.")

    # === AFE Estimate Section ===
    st.subheader("🧮 Enter Well Cost Estimates")

    if os.path.exists(ESTIMATE_FILE):
        with open(ESTIMATE_FILE, "r") as f:
            estimates = json.load(f)
    else:
        estimates = {
            "Drilling AFE": 0,
            "Completion AFE": 0,
            "Estimated Days": 0
        }

    drilling_afe = st.number_input("🛢️ Drilling AFE Total Cost ($)", min_value=0.0, value=float(estimates.get("Drilling AFE", 0)))
    completion_afe = st.number_input("🔧 Completion AFE Total Cost ($)", min_value=0.0, value=float(estimates.get("Completion AFE", 0)))
    estimated_days = st.number_input("Estimated Days (Total)", min_value=0, value=int(estimates.get("Estimated Days", 0)))

    if st.button("💾 Save Estimates"):
        with open(ESTIMATE_FILE, "w") as f:
            json.dump({
                "Drilling AFE": drilling_afe,
                "Completion AFE": completion_afe,
                "Estimated Days": estimated_days
            }, f)
        st.success("Estimates saved.")

    # === Delete Section ===
    st.subheader("🗑️ Delete a Specific Report Entry")

    if os.path.exists(REPORT_LOG):
        df = pd.read_csv(REPORT_LOG)
        df_display = df.copy()
        if not df_display.empty:
            df_display["Entry"] = df["Day #"].astype(str) + " | " + df["Date"].astype(str) + " | " + df["Filename"]
            selected_entry = st.selectbox("Select a row to delete:", df_display["Entry"].tolist())

            if st.button("Delete Selected Entry"):
                selected_row = df_display[df_display["Entry"] == selected_entry]

                if not selected_row.empty:
                    filename_to_delete = selected_row["Filename"].values[0]
                    df = df[df_display["Entry"] != selected_entry]
                    df.to_csv(REPORT_LOG, index=False)

                    file_path = os.path.join(UPLOAD_FOLDER, filename_to_delete)
                    if os.path.exists(file_path):
                        os.remove(file_path)

                    st.success(f"Deleted entry and file: {filename_to_delete}. Please refresh.")
                else:
                    st.error("Could not locate that row.")
        else:
            st.info("No entries to delete.")
    else:
        st.info("No reports uploaded yet.")
