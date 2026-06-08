import streamlit as st
import pandas as pd
import pydeck as pdk
import sys
import os
import math

# Ensure Python can find the backend folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.engine import Farm, Transporter, TomatoDecay, PotatoDecay, MangoDecay, SpinachDecay, WeatherService, Observer

# --- HAVERSINE FORMULA (GPS DISTANCE CALCULATION) ---
def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculates the straight-line distance between two coordinates in km."""
    R = 6371  # Earth radius in kilometers
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

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

# --- CITY COORDINATES DATABASE ---
CITIES = {
    "Nashik": {"lat": 20.00, "lon": 73.78},
    "Mumbai": {"lat": 19.07, "lon": 72.87},
    "Pune": {"lat": 18.52, "lon": 73.85},
    "Nagpur": {"lat": 21.14, "lon": 79.08},
    "Delhi": {"lat": 28.61, "lon": 77.20},
    "Bangalore": {"lat": 12.97, "lon": 77.59}
}

st.sidebar.header("Logistics Parameters")
crop_choice = st.sidebar.selectbox("Select Crop Type", ["Tomatoes", "Potatoes", "Mangoes", "Spinach"])

# Dynamic UI for routing
st.sidebar.subheader("Transit Route")
origin_city = st.sidebar.selectbox("Origin City", list(CITIES.keys()), index=0)
dest_city = st.sidebar.selectbox("Destination Market", list(CITIES.keys()), index=1)

# Auto-calculate distance
exact_distance = calculate_distance(
    CITIES[origin_city]["lat"], CITIES[origin_city]["lon"],
    CITIES[dest_city]["lat"], CITIES[dest_city]["lon"]
)
# Add a 20% multiplier to account for road curvature vs straight-line distance
distance_km = int(exact_distance * 1.2)
st.sidebar.info(f"📍 GPS Calculated Route: **{distance_km} km**")

# --- ECONOMIC PARAMETERS ---
st.sidebar.divider()
st.sidebar.header("Economic Parameters")
market_demand = st.sidebar.select_slider("Current Market Demand", options=["Low", "Normal", "High"], value="Normal")
price_multiplier = {"Low": 0.8, "Normal": 1.0, "High": 1.5}[market_demand]

# --- DYNAMIC LIVE API TOGGLE ---
st.sidebar.divider()
use_live_weather = st.sidebar.checkbox(f"📡 Use Live Weather ({origin_city})", value=True)

if use_live_weather:
    with st.spinner(f"Fetching satellite weather for {origin_city}..."):
        # Pass dynamic coordinates to the backend
        ambient_temp = WeatherService.get_live_temperature(
            origin_city, CITIES[origin_city]["lat"], CITIES[origin_city]["lon"]
        )
    st.sidebar.success(f"Live API Temp ({origin_city}): {ambient_temp}°C")
else:
    ambient_temp = st.sidebar.slider("Manual Ambient Temperature (°C)", 10.0, 45.0, 35.0)

# Map UI selection to the expanded Backend Strategy Pattern
if crop_choice == "Tomatoes": strategy = TomatoDecay()
elif crop_choice == "Potatoes": strategy = PotatoDecay()
elif crop_choice == "Mangoes": strategy = MangoDecay()
elif crop_choice == "Spinach": strategy = SpinachDecay()

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
        current_market_value = batch.get_total_value() * price_multiplier
        history.append({
            "Hour": hour,
            "Quality Score (%)": batch.quality_score,
            "Value (₹)": current_market_value
        })
        batch.degrade(actual_temp, 1)
        
    return pd.DataFrame(history), batch, ui_monitor.alerts, actual_temp

# ==========================================
# 4. A/B SCENARIO DASHBOARD & 2D MAP
# ==========================================
with st.expander(f"🗺️ View Active Transit Route ({origin_city} to {dest_city})", expanded=False):
    
    route_data = pd.DataFrame({
        "origin_lon": [CITIES[origin_city]["lon"]],
        "origin_lat": [CITIES[origin_city]["lat"]],
        "dest_lon": [CITIES[dest_city]["lon"]],
        "dest_lat": [CITIES[dest_city]["lat"]]
    })

    # Use a solid LineLayer instead of a 3D arc for a cleaner navigation look
    line_layer = pdk.Layer(
        "LineLayer",
        data=route_data,
        get_source_position=["origin_lon", "origin_lat"],
        get_target_position=["dest_lon", "dest_lat"],
        get_color=[0, 153, 255, 255],  # Google Maps Navigation Blue
        get_width_min_pixels=5,
    )

    mid_lat = (CITIES[origin_city]["lat"] + CITIES[dest_city]["lat"]) / 2
    mid_lon = (CITIES[origin_city]["lon"] + CITIES[dest_city]["lon"]) / 2

    # Pitch = 0 makes the map completely flat (2D top-down view)
    view_state = pdk.ViewState(
        latitude=mid_lat,
        longitude=mid_lon,
        zoom=5.5,
        pitch=0 
    )

    st.pydeck_chart(pdk.Deck(layers=[line_layer], initial_view_state=view_state, map_style="road"))


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

    # --- PREDICTIVE SHELF-LIFE ANALYTICS ---
    st.divider()
    st.subheader("🔮 ML-Ready Predictive Analytics")
    
    if final_batch_cold.quality_score > 30:
        hourly_drop = strategy.calculate_loss(actual_temp_cold, 1)
        points_remaining = final_batch_cold.quality_score - 30.0
        hours_left = math.floor(points_remaining / hourly_drop) if hourly_drop > 0 else 999
        st.info(f"**Shelf-Life Prediction:** Based on current thermodynamic decay rates, the Cold-Chain cargo has approximately **{hours_left} hours** of viable market life remaining.")
    else:
        st.error("**Shelf-Life Prediction:** The cargo has already spoiled and has 0 hours of market viability remaining.")

    # --- FINAL ROI CALCULATION ---
    st.divider()
    money_saved = final_val_cold - final_val_std
    st.success(f"**Total Financial Savings utilizing Cold-Chain infrastructure: ₹{money_saved:,.2f}**")
    
    # --- ENTERPRISE CSV EXPORT ---
    st.divider()
    st.subheader("📥 Export Enterprise Report")
    st.markdown("Download the raw time-series data for logistical auditing and accounting.")
    
    df_report = pd.DataFrame({
        "Transit Hour": df_standard["Hour"],
        "Open Truck Quality (%)": df_standard["Quality Score (%)"],
        "Cold-Chain Quality (%)": df_cold["Quality Score (%)"],
        "Open Truck Adjusted Value (₹)": df_standard["Value (₹)"],
        "Cold-Chain Adjusted Value (₹)": df_cold["Value (₹)"]
    })
    
    csv_data = df_report.to_csv(index=False).encode('utf-8')
    st.download_button(label="Download Full Supply Chain Audit (.CSV)", data=csv_data, file_name="agrata_logistics_audit.csv", mime="text/csv", type="secondary")