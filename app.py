import streamlit as st
import pandas as pd
from datetime import date
import os
import json
import base64

# Set upload folder to Render's persistent disk mount path
UPLOAD_FOLDER = "/mnt/data/uploaded_reports"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

REPORT_LOG = "/mnt/data/report_log.csv"
ESTIMATE_FILE = "/mnt/data/estimates.json"

# Sidebar navigation with View Reports first
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["View Reports", "Inputs"], index=0)

# ============================
# VIEW REPORTS PAGE
# ============================
if page == "View Reports":
    st.title("Drilling Report Log & Cost Tracking")

    if os.path.exists(REPORT_LOG):
        df = pd.read_csv(REPORT_LOG)

        required_cols = {"Day #", "Daily Cost", "Phase", "Filename", "Date"}
        if required_cols.issubset(df.columns):
            df["Daily Cost"] = pd.to_numeric(df["Daily Cost"], errors="coerce")
            df["Day #"] = pd.to_numeric(df["Day #"], errors="coerce")
            df = df.dropna(subset=["Day #", "Daily Cost"])
            st.dataframe(df)

            st.subheader("Daily Cost vs Drilling Day")
            if not df.empty:
                st.line_chart(df[["Day #", "Daily Cost"]].set_index("Day #"))

            if os.path.exists(ESTIMATE_FILE):
                with open(ESTIMATE_FILE, "r") as f:
                    estimates = json.load(f)

                drilling_afe = estimates.get("Drilling AFE", 0)
                completion_afe = estimates.get("Completion AFE", 0)
                drilling_actual = df[df["Phase"] == "Drilling"]["Daily Cost"].sum()
                completion_actual = df[df["Phase"] == "Completion"]["Daily Cost"].sum()

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### Drilling Cost Summary")
                    st.markdown(f"**AFE:** ${drilling_afe:,.0f}")
                    st.markdown(f"**Actual:** ${drilling_actual:,.0f}")
                    st.markdown(f"**Variance:** ${drilling_actual - drilling_afe:,.0f}")
                with col2:
                    st.markdown("### Completion Cost Summary")
                    st.markdown(f"**AFE:** ${completion_afe:,.0f}")
                    st.markdown(f"**Actual:** ${completion_actual:,.0f}")
                    st.markdown(f"**Variance:** ${completion_actual - completion_afe:,.0f}")

            st.subheader("View Uploaded PDF")
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
            st.error("Missing required columns in report log.")
    else:
        st.warning("No reports uploaded yet.")

# ============================
# INPUTS PAGE
# ============================
elif page == "Inputs":
    st.title("Secure Input Portal")

    password = st.text_input("Enter password to continue", type="password")
    if password != "oilmoney":
        st.warning("Incorrect password.")
        st.stop()

    mode = st.radio("Select Mode", ["Add New Report", "Edit Existing Report"])

    if os.path.exists(REPORT_LOG):
        df = pd.read_csv(REPORT_LOG)
    else:
        df = pd.DataFrame()

    if mode == "Edit Existing Report" and not df.empty:
        df["Entry"] = df["Day #"].astype(str) + " | " + df["Date"] + " | " + df["Filename"]
        selected_entry = st.selectbox("Select a report to edit:", df["Entry"].tolist())
        selected_row = df[df["Entry"] == selected_entry].iloc[0]

        report_date = st.date_input("Report Date", value=pd.to_datetime(selected_row["Date"]).date())
        day_number = st.number_input("Drilling Day #", min_value=1, value=int(selected_row["Day #"]))
        phase = st.selectbox("Phase", ["Drilling", "Completion"], index=0 if selected_row["Phase"] == "Drilling" else 1)
        daily_cost = st.number_input("Daily Cost ($)", min_value=0.0, value=float(selected_row["Daily Cost"]))
        depth = st.number_input("Depth (ft)", min_value=0, value=int(selected_row["Depth (ft)"]))
        notes = st.text_area("Notes", value=selected_row["Notes"])
        uploaded_file = st.file_uploader("Replace PDF (optional)", type="pdf")

        if st.button("Update Report"):
            if uploaded_file:
                filepath = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
                with open(filepath, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                new_filename = uploaded_file.name
            else:
                new_filename = selected_row["Filename"]

            df.loc[df["Entry"] == selected_entry, :] = [
                report_date.strftime("%Y-%m-%d"), day_number, phase, daily_cost, depth, notes, new_filename, selected_entry
            ]
            df.drop(columns=["Entry"], inplace=True)
            df.to_csv(REPORT_LOG, index=False)
            st.success("Report updated successfully.")

    elif mode == "Add New Report":
        st.subheader("Upload Daily Drilling Report")

        report_date = st.date_input("Report Date", value=date.today())
        day_number = st.number_input("Drilling Day #", min_value=1)
        phase = st.selectbox("Phase", ["Drilling", "Completion"])
        daily_cost = st.number_input("Daily Cost ($)", min_value=0.0)
        depth = st.number_input("Depth (ft)", min_value=0)
        notes = st.text_area("Notes")
        uploaded_file = st.file_uploader("Upload PDF", type="pdf")

        if st.button("Submit Report"):
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

    st.subheader("Enter Well Cost Estimates")

    if os.path.exists(ESTIMATE_FILE):
        with open(ESTIMATE_FILE, "r") as f:
            estimates = json.load(f)
    else:
        estimates = {"Drilling AFE": 0, "Completion AFE": 0, "Estimated Days": 0}

    drilling_afe = st.number_input("Drilling AFE Total Cost ($)", min_value=0.0, value=float(estimates.get("Drilling AFE", 0)))
    completion_afe = st.number_input("Completion AFE Total Cost ($)", min_value=0.0, value=float(estimates.get("Completion AFE", 0)))
    estimated_days = st.number_input("Estimated Days (Total)", min_value=0, value=int(estimates.get("Estimated Days", 0)))

    if st.button("Save Estimates"):
        with open(ESTIMATE_FILE, "w") as f:
            json.dump({
                "Drilling AFE": drilling_afe,
                "Completion AFE": completion_afe,
                "Estimated Days": estimated_days
            }, f)
        st.success("Estimates saved.")

    st.subheader("Delete a Specific Report Entry")

    if os.path.exists(REPORT_LOG):
        df = pd.read_csv(REPORT_LOG)
        df_display = df.copy()
        if not df_display.empty:
            df_display["Entry"] = df["Day #"].astype(str) + " | " + df["Date"].astype(str) + " | " + df["Filename"]
            selected_entry = st.selectbox("Select a row to delete:", df_display["Entry"].tolist(), key="delete")

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
