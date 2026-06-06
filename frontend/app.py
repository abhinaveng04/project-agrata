import streamlit as st
import pandas as pd
import sys
import os

# Ensure Python can find the backend folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.engine import Farm, Transporter, TomatoDecay, PotatoDecay, SupplyChainNode

# ==========================================
# 1. UI SETUP & SIDEBAR (INPUTS)
# ==========================================
st.set_page_config(page_title="Agrata Logistics", layout="wide")
st.title("Agrata: Cold-Chain Supply Chain Simulation")
st.markdown("A deterministic OOP engine calculating agricultural decay and financial loss.")

st.sidebar.header("Simulation Parameters")
crop_choice = st.sidebar.selectbox("Select Crop Type", ["Tomatoes", "Potatoes"])
distance_km = st.sidebar.slider("Transit Distance (km)", 50, 1000, 200)
ambient_temp = st.sidebar.slider("Ambient Outside Temperature (°C)", 10.0, 45.0, 35.0)

# Map UI selection to Backend Strategy Pattern
strategy = TomatoDecay() if crop_choice == "Tomatoes" else PotatoDecay()

# ==========================================
# 2. SIMULATION EXECUTION FUNCTION
# ==========================================
def run_simulation(is_refrigerated):
    """Runs the OOP simulation hour-by-hour to generate chart data."""
    farm = Farm("Test Farm", "Origin", 1000)
    batch = farm.harvest_crop(crop_choice, strategy)
    truck = Transporter("Test Truck", distance_km, is_refrigerated)
    
    # Calculate total travel time
    travel_hours = int(distance_km / truck.speed_kmh)
    actual_temp = 4.0 if is_refrigerated else ambient_temp
    
    history = []
    
    # Step through time to record the degradation for the graph
    for hour in range(travel_hours + 1):
        history.append({
            "Hour": hour,
            "Quality Score (%)": batch.quality_score,
            "Value (₹)": batch.get_total_value()
        })
        # Degrade for 1 hour at a time
        batch.degrade(actual_temp, 1)
        
    return pd.DataFrame(history), batch

# ==========================================
# 3. A/B SCENARIO DASHBOARD (OUTPUTS)
# ==========================================
if st.button("Run Supply Chain Simulation", type="primary"):
    
    col1, col2 = st.columns(2)
    
    # --- SCENARIO A: Standard Truck ---
    with col1:
        st.subheader("Scenario A: Open Truck")
        df_standard, final_batch_std = run_simulation(is_refrigerated=False)
        
        # Display the line chart
        st.line_chart(df_standard.set_index("Hour")["Quality Score (%)"], color="#ff4b4b")
        
        st.metric(label="Final Quality", value=f"{final_batch_std.quality_score:.1f}%")
        st.metric(label="Final Value", value=f"₹{final_batch_std.get_total_value():,.2f}")

    # --- SCENARIO B: Cold-Chain Truck ---
    with col2:
        st.subheader("Scenario B: Cold-Chain Transport")
        df_cold, final_batch_cold = run_simulation(is_refrigerated=True)
        
        # Display the line chart
        st.line_chart(df_cold.set_index("Hour")["Quality Score (%)"], color="#00cc96")
        
        st.metric(label="Final Quality", value=f"{final_batch_cold.quality_score:.1f}%")
        st.metric(label="Final Value", value=f"₹{final_batch_cold.get_total_value():,.2f}")

    # --- FINAL ROI CALCULATION ---
    st.divider()
    money_saved = final_batch_cold.get_total_value() - final_batch_std.get_total_value()
    st.success(f"**Total Financial Savings utilizing Cold-Chain infrastructure: ₹{money_saved:,.2f}**")