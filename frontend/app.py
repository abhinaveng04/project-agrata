import streamlit as st
import pandas as pd
import pydeck as pdk
import sys
import os
import math

# Ensure Python can find the backend folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.engine import Farm, Transporter, TomatoDecay, PotatoDecay, WeatherService, Observer

# ==========================================
# 1. UI OBSERVER PATTERN
# ==========================================
class StreamlitMonitor(Observer):
    def __init__(self):
        self.alerts = []
        
    def update(self, batch):
        if batch.quality_score < 60.0 and batch.quality_score > 58.0:
             self.alerts.append(f"🚨 **Critical Alert:** Quality dropped below 60%!")
        elif batch.quality_score == 0.0 and len(self.alerts) < 2:
             self.alerts.append(f"💀 **Fatal Alert:** Cargo has completely spoiled. Write-off required.")

# ==========================================
# 2. UI SETUP & SIDEBAR (INPUTS)
# ==========================================
st.set_page_config(page_title="Agrata Logistics", layout="wide")
st.title("Agrata: Enterprise Logistics & Market Predictor")
st.markdown("A deterministic OOP engine with Live API weather, Geospatial Mapping, and ML-ready Predictive Analytics.")

st.sidebar.header("Logistics Parameters")
crop_choice = st.sidebar.selectbox("Select Crop Type", ["Tomatoes", "Potatoes"])
distance_km = st.sidebar.slider("Transit Distance (km)", 50, 1000, 170)

# --- NEW FEATURE 3: DYNAMIC MARKET PRICING ---
st.sidebar.divider()
st.sidebar.header("Economic Parameters")
market_demand = st.sidebar.select_slider("Current Market Demand", options=["Low", "Normal", "High"], value="Normal")

# Set the price multiplier based on demand
price_multiplier = {"Low": 0.8, "Normal": 1.0, "High": 1.5}[market_demand]

# --- LIVE API TOGGLE ---
st.sidebar.divider()
use_live_weather = st.sidebar.checkbox("📡 Use Live Weather API (Nashik)", value=True)

if use_live_weather:
    with st.spinner("Fetching live satellite weather..."):
        ambient_temp = WeatherService.get_live_temperature("Nashik")
    st.sidebar.success(f"Live API Temperature: {ambient_temp}°C")
else:
    ambient_temp = st.sidebar.slider("Manual Ambient Temperature (°C)", 10.0, 45.0, 35.0)

strategy = TomatoDecay() if crop_choice == "Tomatoes" else PotatoDecay()

# ==========================================
# 3. SIMULATION EXECUTION FUNCTION
# ==========================================
def run_simulation(is_refrigerated):
    farm = Farm("Test Farm", "Origin", 1000)
    batch = farm.harvest_crop(crop_choice, strategy)
    truck = Transporter("Test Truck", distance_km, is_refrigerated)
    
    ui_monitor = StreamlitMonitor()
    batch.attach(ui_monitor)
    
    travel_hours = int(distance_km / truck.speed_kmh)
    actual_temp = 4.0 if is_refrigerated else ambient_temp
    
    history = []
    
    for hour in range(travel_hours + 1):
        # Apply the market demand multiplier to the dynamic value
        current_market_value = batch.get_total_value() * price_multiplier
        history.append({
            "Hour": hour,
            "Quality Score (%)": batch.quality_score,
            "Value (₹)": current_market_value
        })
        batch.degrade(actual_temp, 1)
        
    return pd.DataFrame(history), batch, ui_monitor.alerts, actual_temp

# ==========================================
# 4. A/B SCENARIO DASHBOARD (OUTPUTS)
# ==========================================
# --- NEW FEATURE 2: GEOSPATIAL MAPPING (WITH 3D ROUTE) ---
with st.expander("🗺️ View Active Transit Route (Geospatial Map)", expanded=False):
    # Data defining the start (Nashik) and end (Mumbai) points
    route_data = pd.DataFrame({
        "origin_lon": [73.78],
        "origin_lat": [20.00],
        "dest_lon": [72.87],
        "dest_lat": [19.07]
    })

    # Create a 3D Arc Layer connecting the two cities
    arc_layer = pdk.Layer(
        "ArcLayer",
        data=route_data,
        get_source_position=["origin_lon", "origin_lat"],
        get_target_position=["dest_lon", "dest_lat"],
        get_source_color=[255, 75, 75, 200],  # Red at Origin
        get_target_color=[0, 204, 150, 200],  # Green at Destination
        get_width=5,
        tilt=15
    )

    # Set the camera angle to look at the route with a cool 3D tilt
    view_state = pdk.ViewState(
        latitude=19.53,
        longitude=73.32,
        zoom=7.5,
        pitch=45  # Tilts the map for a 3D effect
    )

    # Render the interactive map
    st.pydeck_chart(pdk.Deck(layers=[arc_layer], initial_view_state=view_state, map_style="road"))

if st.button("Run Supply Chain Simulation", type="primary"):
    
    col1, col2 = st.columns(2)
    
    # --- SCENARIO A: Standard Truck ---
    with col1:
        st.subheader("Scenario A: Open Truck")
        df_standard, final_batch_std, std_alerts, actual_temp_std = run_simulation(is_refrigerated=False)
        
        st.line_chart(df_standard.set_index("Hour")["Quality Score (%)"], color="#ff4b4b")
        final_val_std = final_batch_std.get_total_value() * price_multiplier
        st.metric(label="Final Quality", value=f"{final_batch_std.quality_score:.1f}%")
        st.metric(label="Adjusted Market Value", value=f"₹{final_val_std:,.2f}")
        
        for alert in std_alerts:
            st.error(alert)

    # --- SCENARIO B: Cold-Chain Truck ---
    with col2:
        st.subheader("Scenario B: Cold-Chain Transport")
        df_cold, final_batch_cold, cold_alerts, actual_temp_cold = run_simulation(is_refrigerated=True)
        
        st.line_chart(df_cold.set_index("Hour")["Quality Score (%)"], color="#00cc96")
        final_val_cold = final_batch_cold.get_total_value() * price_multiplier
        st.metric(label="Final Quality", value=f"{final_batch_cold.quality_score:.1f}%")
        st.metric(label="Adjusted Market Value", value=f"₹{final_val_cold:,.2f}")
        
        for alert in cold_alerts:
            st.error(alert)

    # --- NEW FEATURE 1: PREDICTIVE SHELF-LIFE ANALYTICS ---
    st.divider()
    st.subheader("🔮 ML-Ready Predictive Analytics")
    
    if final_batch_cold.quality_score > 30:
        # Calculate hourly degradation rate based on the strategy formula
        hourly_drop = strategy.calculate_loss(actual_temp_cold, 1)
        # Quality points remaining before hitting 30% (spoilage)
        points_remaining = final_batch_cold.quality_score - 30.0
        # Predict hours left
        hours_left = math.floor(points_remaining / hourly_drop) if hourly_drop > 0 else 999
        
        st.info(f"**Shelf-Life Prediction:** Based on current thermodynamic decay rates, the Cold-Chain cargo has approximately **{hours_left} hours** of viable market life remaining before total spoilage.")
    else:
        st.error("**Shelf-Life Prediction:** The cargo has already spoiled and has 0 hours of market viability remaining.")

    # --- FINAL ROI CALCULATION ---
    st.divider()
    money_saved = final_val_cold - final_val_std
    st.success(f"**Total Financial Savings utilizing Cold-Chain infrastructure: ₹{money_saved:,.2f}**")
    # ==========================================
    # 5. ENTERPRISE CSV EXPORT
    # ==========================================
    st.divider()
    st.subheader("📥 Export Enterprise Report")
    st.markdown("Download the raw time-series data for logistical auditing and accounting.")
    
    # Create a combined Master DataFrame for the business report
    df_report = pd.DataFrame({
        "Transit Hour": df_standard["Hour"],
        "Open Truck Quality (%)": df_standard["Quality Score (%)"],
        "Cold-Chain Quality (%)": df_cold["Quality Score (%)"],
        "Open Truck Adjusted Value (₹)": df_standard["Value (₹)"],
        "Cold-Chain Adjusted Value (₹)": df_cold["Value (₹)"]
    })
    
    # Convert the pandas DataFrame to a CSV format
    csv_data = df_report.to_csv(index=False).encode('utf-8')
    
    # Render the interactive download button
    st.download_button(
        label="Download Full Supply Chain Audit (.CSV)",
        data=csv_data,
        file_name="agrata_logistics_audit.csv",
        mime="text/csv",
        type="secondary"
    )