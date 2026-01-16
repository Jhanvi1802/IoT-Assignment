import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Kiln Monitoring Dashboard", layout="wide")

st.title("Kiln IoT Monitoring – Historical Data")
st.write("Historical visualization of sensor data collected from the kiln monitoring system.")

# -------------------------------------------------
# File Upload
# -------------------------------------------------
uploaded_file = st.file_uploader(
    "Upload sensor data (Excel)",
    type=["xlsx"]
)

if uploaded_file is None:
    st.info("Please upload an Excel file to view the dashboard.")
    st.stop()

# -------------------------------------------------
# Load Data
# -------------------------------------------------
data = pd.read_excel(uploaded_file)

st.write("Detected columns:", data.columns.tolist())

# -------------------------------------------------
# Generate Default Timestamp (NO Excel parsing)
# -------------------------------------------------
SAMPLING_INTERVAL_SEC = 10   # assumed logging interval

rows = len(data)
end_time = datetime.now()

data["Time"] = [
    end_time - timedelta(seconds=SAMPLING_INTERVAL_SEC * (rows - i - 1))
    for i in range(rows)
]

# -------------------------------------------------
# Column Mapping (your exact file)
# -------------------------------------------------
temp_col = "Temperature"
hum_col = "Moisture"
gas_col = "CO2"

# -------------------------------------------------
# Basic Data Cleaning (VERY IMPORTANT)
# -------------------------------------------------
for col in [temp_col, hum_col, gas_col]:
    data[col] = data[col].replace(0, pd.NA)
    data[col] = data[col].replace(-1, pd.NA)
    data[col] = data[col].fillna(method="ffill")

# -------------------------------------------------
# Alert Logic
# -------------------------------------------------
TEMP_LIMIT = 450

if data[temp_col].max() > TEMP_LIMIT:
    st.error("🚨 ALERT: Kiln temperature exceeded 450°C")
else:
    st.success("✅ Kiln temperature is within safe operating limits")

# -------------------------------------------------
# KPI Metrics
# -------------------------------------------------
c1, c2, c3 = st.columns(3)

c1.metric("Max Temperature (°C)", round(data[temp_col].max(), 2))
c2.metric("Average Moisture (%)", round(data[hum_col].mean(), 2))
c3.metric("Average CO₂ Level (ppm)", round(data[gas_col].mean(), 2))

st.divider()

# -------------------------------------------------
# Kiln Temperature Plot
# -------------------------------------------------
temp_fig = px.line(
    data,
    x="Time",
    y=temp_col,
    title="Kiln Temperature Trend"
)

temp_fig.update_traces(mode="lines")

temp_fig.add_hline(
    y=TEMP_LIMIT,
    line_dash="dash",
    line_color="red",
    annotation_text="Safety Limit (450°C)"
)

temp_fig.update_layout(
    yaxis_title="Temperature (°C)",
    xaxis_title="Time",
    height=420
)

st.plotly_chart(temp_fig, use_container_width=True)

# -------------------------------------------------
# Moisture Plot
# -------------------------------------------------
hum_fig = px.line(
    data,
    x="Time",
    y=hum_col,
    title="Biomass Moisture Trend"
)

hum_fig.update_traces(mode="lines")

hum_fig.update_layout(
    yaxis_title="Moisture (%)",
    xaxis_title="Time",
    height=420
)

st.plotly_chart(hum_fig, use_container_width=True)

# -------------------------------------------------
# Gas Plot
# -------------------------------------------------
gas_fig = px.line(
    data,
    x="Time",
    y=gas_col,
    title="CO₂ / Gas Concentration Trend"
)

gas_fig.update_traces(mode="lines")

gas_fig.update_layout(
    yaxis_title="CO₂ (ppm)",
    xaxis_title="Time",
    height=420
)

st.plotly_chart(gas_fig, use_container_width=True)

st.divider()

# -------------------------------------------------
# Alert History
# -------------------------------------------------
st.subheader("⚠ Alert History")

if "Alert" in data.columns:
    alert_data = data[data["Alert"].notna()]

    if not alert_data.empty:
        st.dataframe(
            alert_data[["Time", "Alert", "Alert Value"]],
            use_container_width=True,
            height=250
        )
    else:
        st.info("No alert events recorded.")
else:
    st.info("Alert data not available in the uploaded file.")
