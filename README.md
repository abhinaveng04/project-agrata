# 🌐 Agrata: Enterprise Logistics & Cold-Chain Simulation Engine (v1.0.0)

![Python](https://img.shields.io/badge/Python-3.14-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.33-FF4B4B?style=for-the-badge&logo=streamlit)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite)
![Architecture](https://img.shields.io/badge/Architecture-Event--Driven-8A2BE2?style=for-the-badge)
https://agrata.streamlit.app/
**Agrata** is a deterministic, Object-Oriented Decision Support System (DSS) designed to model thermodynamic decay, geospatial routing, and financial forecasting in agricultural supply chains. 

Built as a core engineering initiative at the Noida Institute of Engineering and Technology (NIET), this project bypasses standard static models by integrating live API telemetry, strict data structure enforcement, and gang-of-four design patterns to actively optimize logistics networks and calculate infrastructure ROI.

---

## 🚀 Key Enterprise Features

### 1. Automated Decision Support System (DSS)
* **Capital Expenditure Engine:** The system autonomously crawls historical SQLite transit data to identify the highest point of financial bleeding and mathematically proves the exact ROI of constructing a cold-chain hub in that specific city.
* **Monthly Financial Heatmaps:** Leverages Pandas Dataframe styling and Matplotlib to dynamically generate month-over-month capital destruction reports.
* **What-If Sandbox:** A live evaluator command center that allows supply chain directors to tweak thermodynamic and routing variables in real-time without polluting the primary audit database.

### 2. Software Architecture & Design Patterns
* **The Strategy Pattern:** Decouples crop-specific decay algorithms (e.g., `TomatoDecay`, `SpinachDecay`) from the core engine, allowing for infinite horizontal scalability of commodities.
* **The Observer Pattern (Event-Driven):** Implements an asynchronous event watcher (`StreamlitMonitor`) that subscribes to cargo batches, firing chronological alerts when quality drops below viable thresholds.
* **Singleton Database Connection:** Ensures efficient memory management by maintaining a single persistent SQLite connection thread across the entire application lifecycle.

### 3. Security, Caching, & Fault Tolerance
* **Zero-Trust Authentication:** Secured via `streamlit-authenticator`. Admin passwords are Bcrypt-hashed, cookies are JWT-encrypted, and all secrets are strictly fetched from OS Environment Variables.
* **Microservice Fault Tolerance:** Live API integrations (`urllib`) feature built-in gateway latency handling. If the Open-Meteo or Government Mandi APIs timeout, the engine cleanly intercepts the crash and injects baseline heuristic data to keep the UI lightning fast.
* **In-Memory Caching:** Implements `@st.cache_data` to memoize external API responses, dropping UI reload times from ~8 seconds to milliseconds during interactive slider adjustments.

---

## 🛠️ Local Installation & Setup

Agrata is built with a strictly decoupled architecture (Backend OOP Engine + Frontend Streamlit View).

**1. Clone the repository:**
```bash
git clone [https://github.com/abhinaveng04/project-agrata.git](https://github.com/abhinaveng04/project-agrata.git)
cd project-agrata

```

**2. Install Dependencies:**

```bash
pip install -r requirements.txt

```

**3. Configure Secure Environment Variables:**
Because Agrata is enterprise-secured, you MUST set these variables in your terminal before launching:

```powershell
# Windows PowerShell Example
$env:AGRATA_PASSWORD="your_secure_password"
$env:AGRATA_COOKIE_SECRET="a_very_long_secure_random_string_for_encryption"
$env:DATA_GOV_IN_KEY="your_api_key_from_data_gov_in"

```

**4. Launch the Engine:**

```bash
python -m streamlit run frontend/app.py

```

---

## ☁️ Cloud Deployment (Streamlit Community Cloud)

Agrata is fully optimized for persistent Linux container deployment via Streamlit Community Cloud.

## 📈 Future Roadmap (Version 2.0)

* **Predictive ML Integration:** Swap out current mathematical heuristics for a trained machine learning model to predict shelf-life and market demand dynamically.
* **IoT Sensor Hooks:** Replace Open-Meteo API data with live payload feeds from in-transit BLE/LoRa refrigeration sensors.

**Architected and Developed by Abhinav Gupta & Team.**
