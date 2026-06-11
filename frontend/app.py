import streamlit as st
import pandas as pd
import pydeck as pdk
import sys
import os
import math
import streamlit_authenticator as stauth

# Ensure Python can find the backend folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.engine import Farm, Transporter, TomatoDecay, PotatoDecay, MangoDecay, SpinachDecay, CapsicumDecay, LitchiDecay, OrangeDecay, RiceDecay, WheatDecay, BananaDecay, AppleDecay, OnionDecay, WeatherService, MandiService, Observer, BASE_VALUE_PER_KG
from backend.database import db

# --- API CACHING LAYER ---
@st.cache_data(ttl=300)
def get_cached_mandi_price(crop_name):
    return MandiService.get_live_mandi_price(crop_name)

@st.cache_data(ttl=300)
def get_cached_weather(city, lat, lon):
    return WeatherService.get_live_temperature(city, lat, lon)

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
        self.alerts = set() # Use a set to prevent duplicates
        
    def update(self, batch):
        if 0.0 < batch.quality_score < 60.0:
             self.alerts.add(f"🚨 {batch.crop_type} quality dropped to {batch.quality_score:.1f}%!")
             
        elif batch.quality_score < 1.0:
             self.alerts.add(f"💀 {batch.crop_type} has completely spoiled. Write-off required.")

# ==========================================
# 2. UI SETUP & ENTERPRISE AUTHENTICATION
# ==========================================
st.set_page_config(page_title="Agrata Logistics", layout="wide")

password = os.environ.get("AGRATA_PASSWORD")
secret_key = os.environ.get("AGRATA_COOKIE_SECRET")

if not password or not secret_key:
    st.error("SECURITY HALT: Environment credentials not set.")
    st.stop()

hashed_passwords = stauth.Hasher.hash_list([password])

credentials = {
    "usernames": {
        "admin": {
            "email": "admin@agrata.com",
            "name": "System Admin",
            "password": hashed_passwords[0]
        }
    }
}

# Initialize the authenticator 
authenticator = stauth.Authenticate(
    credentials,
    "agrata_auth_cookie",
    secret_key,
    cookie_expiry_days=1
)

# Render the official login module
authenticator.login()

# Check the session state instead of the old variables
if st.session_state["authentication_status"] is False:
    st.error("Invalid credentials. Authorization denied.")
    st.stop()
elif st.session_state["authentication_status"] is None:
    st.info("🔒 Please authenticate to access the enterprise simulation engine.")
    st.stop()

# --- MAIN DASHBOARD (Only renders if authenticated) ---
# Add a logout button to the sidebar so you can cleanly exit the session
authenticator.logout("Logout", "sidebar")

# Dynamically pull the admin's name from the secure session state
st.title(f"Welcome, {st.session_state['name']}")
st.markdown("Agrata Enterprise | A deterministic OOP engine with Live API weather, Geospatial Mapping, and ML-ready Predictive Analytics.")

# ==========================================
# 3. ENTERPRISE KPI DASHBOARD
# ==========================================
try:
    df_kpi = db.get_all_runs()
    if not df_kpi.empty:
        st.subheader("📊 Global Supply Chain Analytics")
        
        # Create 4 columns for the metric cards
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        # 1. Total Routes
        total_routes = len(df_kpi)
        
        # 2. Avg Spoilage % (100% - Avg Quality)
        avg_spoilage = 100.0 - df_kpi["final_quality"].mean()
        
        # 3. Estimated Financial Loss (Potential Max Value vs Actual Value)
        valid_runs = df_kpi[df_kpi["final_quality"] >= 1.0]
        potential_value = (valid_runs["market_value"] / (valid_runs["final_quality"] / 100.0)).sum()
        actual_value = valid_runs["market_value"].sum()
        est_loss = potential_value - actual_value
        
        # Add an estimated ₹25,000 baseline write-off penalty for fully spoiled cargo (0%)
        dead_runs = len(df_kpi[df_kpi["final_quality"] == 0])
        est_loss += dead_runs * 25000  
        
        # 4. Alerts Fired (Any run that dipped below 60% quality)
        alerts_fired = len(df_kpi[df_kpi["final_quality"] < 60.0])
        
        # Render the metrics
        kpi1.metric(label="Total Transit Routes", value=f"{total_routes:,}")
        kpi2.metric(label="Avg Fleet Spoilage", value=f"{avg_spoilage:.1f}%")
        kpi3.metric(label="Estimated Financial Loss", value=f"₹{est_loss:,.2f}")
        kpi4.metric(label="Critical Alerts Fired", value=f"{alerts_fired}")
        
        st.divider()

        # ---Spoilage Cost Heatmap ---
        st.subheader("Financial Spoilage by Commodity")
        st.markdown("Historical analysis of total capital lost to thermodynamic decay per crop type.")
        
        # Calculate the exact loss for every single row in the database
        def calculate_row_loss(row):
            if row["final_quality"] >=1.0:
                potential = row["market_value"] / (row["final_quality"] / 100.0)
                return potential - row["market_value"]
            return 25000.0  # Standard write-off penalty for 0% quality
            
        df_kpi["Spoilage Loss (₹)"] = df_kpi.apply(calculate_row_loss, axis=1)
        
        # Group by crop type and sum the losses
        loss_df = df_kpi.groupby("crop_type")["Spoilage Loss (₹)"].sum()
        
        # Sort values so the biggest losers are on the left
        loss_df = loss_df.sort_values(ascending=False)
        
        # Render the bar chart with a danger-red color
        st.bar_chart(loss_df, color="#ff4b4b", height=350)
        
        st.divider()

# --- NEW: Monthly Loss Report ---
        st.subheader("📅 Monthly Financial & Material Loss Report")
        st.markdown("Aggregated logistical efficiency, tracking physical spoilage and capital destruction month-over-month.")

        # 1. Format the timestamp and calculate physical material lost (Baseline is 1000kg)
        df_kpi["timestamp"] = pd.to_datetime(df_kpi["timestamp"])
        df_kpi["Month"] = df_kpi["timestamp"].dt.strftime('%B %Y')
        df_kpi["Kg Lost"] = 1000 * (1 - (df_kpi["final_quality"] / 100.0))

        # 2. Group core metrics by Month
        monthly_summary = df_kpi.groupby("Month").agg(
            Total_Routes=("run_id", "count"),
            Total_Kg_Lost=("Kg Lost", "sum"),
            Total_Loss_INR=("Spoilage Loss (₹)", "sum")
        ).reset_index()

        # 3. Find the worst performing commodity per month
        monthly_crop_loss = df_kpi.groupby(["Month", "crop_type"])["Spoilage Loss (₹)"].sum().reset_index()
        # Find the row index of the maximum financial loss for each month
        idx = monthly_crop_loss.groupby("Month")["Spoilage Loss (₹)"].idxmax()
        worst_crops = monthly_crop_loss.loc[idx]

        # 4. Merge the data and clean up the column names for presentation
        monthly_report = pd.merge(monthly_summary, worst_crops[["Month", "crop_type"]], on="Month")
        monthly_report.rename(columns={
            "Total_Routes": "Total Routes",
            "Total_Kg_Lost": "Material Lost (kg)",
            "Total_Loss_INR": "Financial Loss (₹)",
            "crop_type": "Worst Commodity"
        }, inplace=True)

        # 5. Sort chronologically (newest months at the top)
        monthly_report["Month_DT"] = pd.to_datetime(monthly_report["Month"], format='%B %Y')
        monthly_report = monthly_report.sort_values(by="Month_DT", ascending=False).drop(columns=["Month_DT"])

        # 6. Apply conditional styling to turn the Financial Loss column into a heatmap
        styled_report = monthly_report.style.format({
            "Material Lost (kg)": "{:,.1f} kg",
            "Financial Loss (₹)": "₹{:,.2f}"
        }).background_gradient(subset=["Financial Loss (₹)"], cmap="Reds")

        # Render the formatted table
        st.dataframe(styled_report, hide_index=True, use_container_width=True)
        
        st.divider()

# --- NEW: AI Investment Recommendation Engine ---
        st.subheader("💡 Strategic Investment Engine")
        st.markdown("Automated capital expenditure recommendations based on historical thermodynamic decay patterns.")
        
        # 1. Isolate the runs that used Open Trucks
        open_truck_runs = df_kpi[df_kpi["transport_type"] == "Open Truck"]
        
        if not open_truck_runs.empty:
            # 2. Find the origin city bleeding the most cash from open trucks
            city_losses = open_truck_runs.groupby("origin_city")["Spoilage Loss (₹)"].sum().sort_values(ascending=False)
            worst_city = city_losses.index[0]
            current_loss = city_losses.iloc[0]
            
            # 3. Calculate what the loss WOULD have been if they used Cold-Chain
            cc_runs = df_kpi[df_kpi["transport_type"] == "Cold-Chain"]
            if not cc_runs.empty:
                # Find average cold-chain loss percentage
                cc_avg_loss_pct = (100.0 - cc_runs["final_quality"].mean()) / 100.0
            else:
                cc_avg_loss_pct = 0.05 # Fallback to 5% standard cold-chain loss
                
            # Reconstruct the maximum potential revenue for those specific failed runs
            worst_city_runs = open_truck_runs[open_truck_runs["origin_city"] == worst_city]
            potential_rev = worst_city_runs["market_value"].sum() + current_loss
            
            # 4. The ROI Math: Current Loss - Projected Cold Chain Loss
            projected_cc_loss = potential_rev * cc_avg_loss_pct
            annual_savings = current_loss - projected_cc_loss
            
            # 5. Render the Recommendation Card
            if annual_savings > 0:
                st.info(f"**Primary Recommendation:** Construct a centralized Cold Storage Hub in **{worst_city}**.")
                st.markdown(f"**Data Justification:** Routes originating from {worst_city} using standard transport have historically resulted in **₹{current_loss:,.2f}** of thermodynamic write-offs. By migrating these initial-stage routes to a cold-chain pipeline, projected spoilage would drop to **₹{projected_cc_loss:,.2f}**, unlocking an estimated **₹{annual_savings:,.2f}** in preserved capital.")
                
                # Big visually striking metric
                st.metric("Projected Capital Preserved (ROI)", f"₹{annual_savings:,.2f}", delta="Action Required", delta_color="normal")
            else:
                st.success("Current logistics network is highly optimized. No major capital expenditure recommended at this time.")
        
        st.divider()

except Exception as e:
    st.error(f"System Error: {e}")
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

CROPS = ["Tomatoes", "Potatoes", "Mangoes", "Spinach", 
         "Capsicum", "Litchi", "Orange", "Rice", 
         "Wheat", "Banana", "Apple", "Onion"]
crop_choice = st.sidebar.selectbox("Select Crop Type", CROPS)

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

# --- Automated live pricing retrieval ---
with st.spinner(f"Querying National Mandi index for {crop_choice}..."):
    base_mandi_price =get_cached_mandi_price(crop_choice)

st.sidebar.success(f"Market Valuation Price: **₹{base_mandi_price:.2f}/kg**")

# --- DYNAMIC LIVE API TOGGLE ---
st.sidebar.divider()
use_live_weather = st.sidebar.checkbox(f"📡 Use Live Weather ({origin_city})", value=True)

if use_live_weather:
    with st.spinner(f"Fetching satellite weather for {origin_city}..."):
        # Pass dynamic coordinates to the backend
        ambient_temp =get_cached_weather(
            origin_city, CITIES[origin_city]["lat"], CITIES[origin_city]["lon"]
        )
    st.sidebar.success(f"Live API Temp ({origin_city}): {ambient_temp}°C")
else:
    ambient_temp = st.sidebar.slider("Manual Ambient Temperature (°C)", 10.0, 45.0, 35.0)

# Map UI selection to the expanded Backend Strategy Pattern safely
STRATEGY_MAP = {
    "Tomatoes": TomatoDecay, "Potatoes": PotatoDecay,
    "Mangoes": MangoDecay,  "Spinach":  SpinachDecay,
    "Capsicum": CapsicumDecay, "Litchi": LitchiDecay,
    "Orange": OrangeDecay, "Rice": RiceDecay,
    "Wheat": WheatDecay, "Banana": BananaDecay,
    "Apple": AppleDecay, "Onion": OnionDecay
}

strategy = STRATEGY_MAP.get(crop_choice, TomatoDecay)()

# ==========================================
# 3.1 SIMULATION EXECUTION FUNCTION
# ==========================================
def run_simulation(is_refrigerated):
    farm = Farm("Test Farm", "Origin", 1000)
    batch = farm.harvest_crop(crop_choice, strategy)
    truck = Transporter("Test Truck", distance_km, is_refrigerated)
    
    ui_monitor = StreamlitMonitor()
    batch.attach(ui_monitor)
    
    # FIX: Mirror the backend ceiling logic
    travel_hours = math.ceil(distance_km / truck.speed_kmh)
    actual_temp = 4.0 if is_refrigerated else ambient_temp
    
    history = []

    history.append({
        "Hour": 0,
        "Quality Score (%)": batch.quality_score,
        "Value (₹)": batch.get_total_value() * price_multiplier
    })

    for hour in range(1, travel_hours + 1):
        batch.degrade(actual_temp, 1)
        history.append({
            "Hour": hour,
            "Quality Score (%)": batch.quality_score,
            "Value (₹)": batch.get_total_value() * price_multiplier
        })
        
    return pd.DataFrame(history), batch, ui_monitor.alerts, actual_temp

# ==========================================
# 4. A/B SCENARIO DASHBOARD & DYNAMIC MAPS
# ==========================================
def generate_dynamic_map(final_quality):
    """Creates a 3D Arc map that fades from Green to Red based on decay."""
    # Map final quality score to RGB colors
    if final_quality >= 75.0:
        target_color = [0, 204, 150, 255]  # Green (Fresh)
    elif final_quality >= 40.0:
        target_color = [255, 204, 0, 255]  # Yellow (Warning)
    else:
        target_color = [255, 75, 75, 255]  # Red (Spoiled)

    route_data = pd.DataFrame({
        "origin_lon": [CITIES[origin_city]["lon"]],
        "origin_lat": [CITIES[origin_city]["lat"]],
        "dest_lon": [CITIES[dest_city]["lon"]],
        "dest_lat": [CITIES[dest_city]["lat"]]
    })

    # The Arc Layer creates a beautiful gradient from origin to destination
    arc_layer = pdk.Layer(
        "ArcLayer",
        data=route_data,
        get_source_position=["origin_lon", "origin_lat"],
        get_target_position=["dest_lon", "dest_lat"],
        get_source_color=[0, 204, 150, 255],  # Always starts fresh at the farm
        get_target_color=target_color,        # Ends at the decayed color
        get_width=8,
        tilt=15
    )

    mid_lat = (CITIES[origin_city]["lat"] + CITIES[dest_city]["lat"]) / 2
    mid_lon = (CITIES[origin_city]["lon"] + CITIES[dest_city]["lon"]) / 2

    # Switch to dark mode map to make the bright colors pop
    view_state = pdk.ViewState(latitude=mid_lat, longitude=mid_lon, zoom=5.2, pitch=40)
    return pdk.Deck(layers=[arc_layer], initial_view_state=view_state, map_style="dark")

def display_route_pnl(final_batch, distance, is_refrigerated, price_mult, live_mandi_rate):
    """Calculates and displays a financial P&L statement for the transit route."""
    initial_kg = final_batch.quantity
    base_price = live_mandi_rate * price_mult
    potential_revenue = initial_kg * base_price
    
    # Normalize the backend value logic to match the live telemetry stream
    actual_revenue = (final_batch.get_total_value() * price_mult / BASE_VALUE_PER_KG) * live_mandi_rate
    spoilage_loss = potential_revenue - actual_revenue
    
    fuel_rate_per_km = 28.0 if is_refrigerated else 18.0
    fuel_cost = distance * fuel_rate_per_km
    
    net_profit = actual_revenue - fuel_cost
    margin_percent = (net_profit / potential_revenue) * 100 if potential_revenue > 0 else 0.0

    st.markdown("#### 📋 Route P&L Statement")
    pnl_df = pd.DataFrame({
        "Financial Line Item": ["Potential Revenue (100% Yield)", "Spoilage Loss", "Transit Fuel Cost"],
        "Amount (₹)": [f"₹{potential_revenue:,.2f}", f"-₹{spoilage_loss:,.2f}", f"-₹{fuel_cost:,.2f}"]
    })
    st.dataframe(pnl_df, hide_index=True, use_container_width=True)
    
    if net_profit > 0:
        st.success(f"**Net Profit:** ₹{net_profit:,.2f} ({margin_percent:.1f}% Margin)")
    else:
        st.error(f"**Net Loss:** ₹{net_profit:,.2f} ({margin_percent:.1f}% Margin)")
        
    return net_profit

if st.button("Run Supply Chain Simulation", type="primary"):
    
    col1, col2 = st.columns(2)
    
    # --- SCENARIO A: Standard Truck ---
    with col1:
        st.subheader("Scenario A: Open Truck")
        df_standard, final_batch_std, std_alerts, actual_temp_std = run_simulation(is_refrigerated=False)
        
        if origin_city == dest_city:
            st.info("Origin and destination are the same city — no transit route to display.")
        else:
            st.pydeck_chart(generate_dynamic_map(final_batch_std.quality_score))

        st.line_chart(df_standard.set_index("Hour")["Quality Score (%)"], color="#ff4b4b")
        
        # Inject the new P&L Statement
        net_profit_std = display_route_pnl(final_batch_std, distance_km, False, price_multiplier, base_mandi_price)
        
        for alert in std_alerts:
            st.error(alert)

    # --- SCENARIO B: Cold-Chain Transport ---
    with col2:
        st.subheader("Scenario B: Cold-Chain")
        df_cold, final_batch_cold, cold_alerts, actual_temp_cold = run_simulation(is_refrigerated=True)
        
        if origin_city == dest_city:
            st.info("Origin and destination are the same city — no transit route to display.")
        else:
            st.pydeck_chart(generate_dynamic_map(final_batch_cold.quality_score))
            
        st.line_chart(df_cold.set_index("Hour")["Quality Score (%)"], color="#00cc96")
        
        # Inject the new P&L Statement
        net_profit_cold = display_route_pnl(final_batch_cold, distance_km, True, price_multiplier, base_mandi_price)
        
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
    money_saved = net_profit_cold - net_profit_std
    if money_saved > 0:
        st.success(f"**Total Financial Advantage of Cold-Chain:** ₹{money_saved:,.2f} extra profit.")
    else:
        st.warning(f"**Cold-Chain Unnecessary:** Standard transport is more profitable by ₹{abs(money_saved):,.2f} due to fuel costs.")

    # ---------------------------------------------
    # NEW: WRITE SECURE LOGS TO SQLITE
    # ---------------------------------------------
    final_val_std = (final_batch_std.get_total_value() * price_multiplier / BASE_VALUE_PER_KG) * base_mandi_price
    final_val_cold = (final_batch_cold.get_total_value() * price_multiplier / BASE_VALUE_PER_KG) * base_mandi_price
    
    db.log_run(origin_city, dest_city, crop_choice, "Open Truck", distance_km, final_batch_std.quality_score, final_val_std)
    db.log_run(origin_city, dest_city, crop_choice, "Cold-Chain", distance_km, final_batch_cold.quality_score, final_val_cold)
    
    # ==========================================
    # 6. FINANCIAL SANDBOX (BREAK-EVEN ANALYSIS)
    # ==========================================
    st.divider()
    st.subheader("Financial Sandbox: Break-Even Analysis")
    st.markdown("Dynamically model at what exact spoilage percentage the current transit route becomes unprofitable.")

    # Interactive slider for the Mandi (Market) Price
    custom_mandi_price = st.slider(
        "Simulate Mandi Price (₹/kg) for 100% Quality", 
        min_value=10.0, max_value=200.0, 
        value=float(base_mandi_price), # FIX: Pre-fill with actual live price
        step=2.0
    )

    # Generate the theoretical curve
    spoilage_data = []
    baseline_quantity = 1000  # Standard farm harvest

    for spoilage_pct in range(0, 101, 2):
        simulated_quality = 100.0 - spoilage_pct
        
        # Apply the exact thermodynamic pricing logic from the backend
        if simulated_quality < 30:
            adjusted_price = 0.0
        else:
            adjusted_price = custom_mandi_price * (simulated_quality / 100.0)
            
        revenue = baseline_quantity * adjusted_price
        
        # Calculate for both transport types to show a dual-line chart
        profit_open = revenue - (distance_km * 18.0)
        profit_cold = revenue - (distance_km * 28.0)
        
        spoilage_data.append({
            "Spoilage (%)": spoilage_pct,
            "Open Truck Profit (₹)": profit_open,
            "Cold-Chain Profit (₹)": profit_cold,
            "Break-Even Line (₹0)": 0.0  # Creates a flat baseline on the chart
        })

    # Convert to DataFrame and set the X-Axis
    df_breakeven = pd.DataFrame(spoilage_data).set_index("Spoilage (%)")

    # Display the chart with specific brand colors
    st.line_chart(df_breakeven, color=["#ff4b4b", "#00cc96", "#ffffff"], height=350)

    # Calculate and display the exact mathematical break-even points
    try:
        # Find the first index (Spoilage %) where profit drops below zero
        be_open = df_breakeven[df_breakeven["Open Truck Profit (₹)"] <= 0].index[0]
        be_cold = df_breakeven[df_breakeven["Cold-Chain Profit (₹)"] <= 0].index[0]
        
        be_col1, be_col2 = st.columns(2)
        be_col1.warning(f"📉 **Open Truck Break-Even:** Unprofitable at **{be_open}% Spoilage**.")
        be_col2.warning(f"📉 **Cold-Chain Break-Even:** Unprofitable at **{be_cold}% Spoilage** (Requires a higher quality yield to offset the heavier fuel costs).")
    except IndexError:
        st.success("This specific route is highly profitable. It never breaks even under these market parameters unless the cargo completely spoils!")

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

# ==========================================
# 5. ENTERPRISE DATA WAREHOUSE (SQLITE)
# ==========================================
st.divider()
st.subheader("🗄️ Enterprise Data Warehouse")

try:
    df_history = db.get_all_runs()
    if not df_history.empty:
        # Display the SQL data visually in Streamlit
        st.dataframe(df_history, use_container_width=True, hide_index=True)
        
        # Add a purge tool for clean demo resets
        if st.button("Purge Database Logs", type="secondary"):
            db.purge()
            st.rerun()
    else:
        st.info("The database is currently empty. Run a simulation to generate persistent logs.")
except Exception as e:
    st.error(f"Database Connection Error: {e}")

# ==========================================
# 6. THE EVALUATOR SANDBOX (WHAT-IF SIMULATOR)
# ==========================================
st.divider()
st.subheader("🎛️ The 'What-If' Command Center")
st.markdown("Live Evaluator Sandbox: Adjust transit variables in real-time to forecast logistical outcomes and financial viability without triggering database audits.")

# Container to hold the split UI
with st.container():
    wi_col1, wi_col2 = st.columns([1, 1.5])
    
    with wi_col1:
        st.markdown("#### ⚙️ Scenario Inputs")
        
        # Use columns inside the left panel for a tighter, dashboard-style UI
        wi_r1, wi_r2 = st.columns(2)
        wi_origin = wi_r1.selectbox("Origin", list(CITIES.keys()), index=1, key="wi_ori")
        wi_dest = wi_r2.selectbox("Destination", list(CITIES.keys()), index=4, key="wi_dest")
        
        # Use the global map instead of the sandbox-only map
        wi_crop = st.selectbox("Commodity", list(STRATEGY_MAP.keys()), index=3, key="wi_crop")
        wi_vehicle = st.radio("Transport Fleet", ["Standard Open Truck", "Cold-Chain Reefer"], horizontal=True, key="wi_veh")

        # Time of day directly impacts ambient thermal baseline
        wi_time = st.select_slider(
            "Departure Time (Thermal Impact)", 
            options=["Midnight (18°C)", "Morning (24°C)", "High Noon (38°C)"], 
            value="High Noon (38°C)"
        )
        
    with wi_col2:
        st.markdown("#### 📊 Live Projection")
        
    # --- 1. Map Inputs to Engine Variables ---
        wi_dist = int(calculate_distance(CITIES[wi_origin]["lat"], CITIES[wi_origin]["lon"], CITIES[wi_dest]["lat"], CITIES[wi_dest]["lon"]) * 1.2)
        wi_strategy = STRATEGY_MAP[wi_crop]()
        wi_is_ref = "Cold-Chain" in wi_vehicle
        wi_ambient = {"Midnight (18°C)": 18.0, "Morning (24°C)": 24.0, "High Noon (38°C)": 38.0}[wi_time]
        wi_actual_temp = 4.0 if wi_is_ref else wi_ambient
        wi_travel_hours = math.ceil(wi_dist / 50) 
        
        # --- 2. Run Isolated Simulation ---
        wi_farm = Farm("Sandbox Farm", wi_origin, 1000)
        wi_batch = wi_farm.harvest_crop(wi_crop, wi_strategy)
        
        for _ in range(wi_travel_hours + 1):
            wi_batch.degrade(wi_actual_temp, 1)
            
        # --- 3. Fast Financial Math ---
        wi_base_prices = {"Tomatoes": 32.0, "Mangoes": 85.0, "Spinach": 25.0, "Litchi": 120.0, "Wheat": 28.0, "Apple": 115.0}
        wi_price = wi_base_prices.get(wi_crop, 40.0)
        wi_potential_rev = 1000 * wi_price
        wi_actual_rev = (wi_batch.get_total_value() / 40.0) * wi_price
        wi_spoilage_loss = wi_potential_rev - wi_actual_rev
        wi_fuel_cost = wi_dist * (28.0 if wi_is_ref else 18.0)
        wi_net_profit = wi_actual_rev - wi_fuel_cost
        wi_margin = (wi_net_profit / wi_potential_rev) * 100 if wi_potential_rev > 0 else 0.0
        
        # --- 4. Render Output Cards ---
        st.info(f"**Route Details:** {wi_origin} to {wi_dest} (**{wi_dist} km**) | Estimated Transit: **{wi_travel_hours} hours**")
        
        res_col1, res_col2 = st.columns(2)
        
        # Dynamic Quality Metric Emoji
        if wi_batch.quality_score >= 70:
            qual_color = "🟢"
        elif wi_batch.quality_score >= 30:
            qual_color = "🟡"
        else:
            qual_color = "🔴"
            
        res_col1.metric(
            label=f"{qual_color} Final Cargo Quality", 
            value=f"{wi_batch.quality_score:.1f}%", 
            delta=f"-{100 - wi_batch.quality_score:.1f}% Spoilage", 
            delta_color="inverse"
        )
        
        # Financial Metric
        res_col2.metric(
            label="Net Profit (After Fuel)", 
            value=f"₹{wi_net_profit:,.2f}", 
            delta=f"{wi_margin:.1f}% Margin"
        )
        
        # Visual Progress Bar
        st.progress(int(wi_batch.quality_score), text="Final Market Viability Score")
        
        if wi_batch.quality_score == 0:
            st.error(f"**Total Write-Off:** Cargo spoiled entirely due to **{wi_travel_hours} hours** of exposure at **{wi_actual_temp}°C**.")