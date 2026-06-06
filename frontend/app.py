import streamlit as st
import pandas as pd
import sys
import os

# Ensure Python can find the backend folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.engine import Farm, Transporter, TomatoDecay, PotatoDecay, WeatherService, Observer

# ==========================================
# 1. UI OBSERVER PATTERN
# ==========================================
class StreamlitMonitor(Observer):
    """A custom observer that catches alerts and saves them to display in the UI."""
    def __init__(self):
        self.alerts = []
        
    def update(self, batch):
        # Only capture the alert the first time it drops below 60 to avoid spamming the UI
        if batch.quality_score < 60.0 and batch.quality_score > 58.0:
             self.alerts.append(f"🚨 **Critical Alert:** Quality dropped below 60%!")
        elif batch.quality_score == 0.0 and len(self.alerts) < 2:
             self.alerts.append(f"💀 **Fatal Alert:** Cargo has completely spoiled. Write-off required.")

# ==========================================
# 2. UI SETUP & SIDEBAR (INPUTS)
# ==========================================
st.set_page_config(page_title="Agrata Logistics", layout="wide")
st.title("Agrata: Cold-Chain Supply Chain Simulation")
st.markdown("A deterministic OOP engine utilizing Live API weather and Event-Driven Architecture.")

st.sidebar.header("Simulation Parameters")
crop_choice = st.sidebar.selectbox("Select Crop Type", ["Tomatoes", "Potatoes"])
distance_km = st.sidebar.slider("Transit Distance (km)", 50, 1000, 350)

# --- LIVE API TOGGLE ---
st.sidebar.divider()
use_live_weather = st.sidebar.checkbox("📡 Use Live Weather API (Nashik)", value=True)

if use_live_weather:
    with st.spinner("Fetching live satellite weather..."):
        ambient_temp = WeatherService.get_live_temperature("Nashik")
    st.sidebar.success(f"Live API Temperature: {ambient_temp}°C")
else:
    ambient_temp = st.sidebar.slider("Manual Ambient Temperature (°C)", 10.0, 45.0, 35.0)

# Map UI selection to Backend Strategy Pattern
strategy = TomatoDecay() if crop_choice == "Tomatoes" else PotatoDecay()

# ==========================================
# 3. SIMULATION EXECUTION FUNCTION
# ==========================================
def run_simulation(is_refrigerated):
    farm = Farm("Test Farm", "Origin", 1000)
    batch = farm.harvest_crop(crop_choice, strategy)
    truck = Transporter("Test Truck", distance_km, is_refrigerated)
    
    # Attach our UI Observer to the batch!
    ui_monitor = StreamlitMonitor()
    batch.attach(ui_monitor)
    
    travel_hours = int(distance_km / truck.speed_kmh)
    actual_temp = 4.0 if is_refrigerated else ambient_temp
    
    history = []
    
    for hour in range(travel_hours + 1):
        history.append({
            "Hour": hour,
            "Quality Score (%)": batch.quality_score,
            "Value (₹)": batch.get_total_value()
        })
        batch.degrade(actual_temp, 1)
        
    return pd.DataFrame(history), batch, ui_monitor.alerts

# ==========================================
# 4. A/B SCENARIO DASHBOARD (OUTPUTS)
# ==========================================
if st.button("Run Supply Chain Simulation", type="primary"):
    
    col1, col2 = st.columns(2)
    
    # --- SCENARIO A: Standard Truck ---
    with col1:
        st.subheader("Scenario A: Open Truck")
        df_standard, final_batch_std, std_alerts = run_simulation(is_refrigerated=False)
        
        st.line_chart(df_standard.set_index("Hour")["Quality Score (%)"], color="#ff4b4b")
        st.metric(label="Final Quality", value=f"{final_batch_std.quality_score:.1f}%")
        st.metric(label="Final Value", value=f"₹{final_batch_std.get_total_value():,.2f}")
        
        # Display the Observer Alerts
        for alert in std_alerts:
            st.error(alert)

    # --- SCENARIO B: Cold-Chain Truck ---
    with col2:
        st.subheader("Scenario B: Cold-Chain Transport")
        df_cold, final_batch_cold, cold_alerts = run_simulation(is_refrigerated=True)
        
        st.line_chart(df_cold.set_index("Hour")["Quality Score (%)"], color="#00cc96")
        st.metric(label="Final Quality", value=f"{final_batch_cold.quality_score:.1f}%")
        st.metric(label="Final Value", value=f"₹{final_batch_cold.get_total_value():,.2f}")
        
        for alert in cold_alerts:
            st.error(alert)

    # --- FINAL ROI CALCULATION ---
    st.divider()
    money_saved = final_batch_cold.get_total_value() - final_batch_std.get_total_value()
    st.success(f"**Total Financial Savings utilizing Cold-Chain infrastructure: ₹{money_saved:,.2f}**")