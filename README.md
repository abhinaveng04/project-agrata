# 🌐 Agrata: Enterprise Logistics & Cold-Chain Simulation Engine

![Python](https://img.shields.io/badge/Python-3.14-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28-FF4B4B?style=for-the-badge&logo=streamlit)
![Architecture](https://img.shields.io/badge/Architecture-Event--Driven-8A2BE2?style=for-the-badge)

**Agrata** is a deterministic, Object-Oriented simulation engine designed to model thermodynamic decay, geospatial routing, and financial forecasting in agricultural supply chains. 

Built as a core engineering initiative at the Noida Institute of Engineering and Technology (NIET), this project bypasses standard static models by integrating live API telemetry, strict data structure enforcement, and gang-of-four design patterns to simulate real-world logistics networks.

## 🚀 System Architecture & Core Features

### 1. Advanced Data Structures & Algorithms
* **FIFO Queue Management:** Utilizes Python's `collections.deque` for $O(1)$ constant-time inventory dispatching, ensuring strict First-In-First-Out (FIFO) cargo processing across all supply chain nodes.
* **Haversine Distance Algorithm:** Implements spherical trigonometry to dynamically calculate exact point-to-point GPS distances between geographic market coordinates.
* **Deterministic Decay Modeling:** Mathematical degradation heuristics calculate perishable viability based on thermal variables and transit duration.

### 2. Software Design Patterns
* **The Strategy Pattern:** Decouples crop-specific decay algorithms (e.g., `TomatoDecay`, `SpinachDecay`, `MangoDecay`) from the core engine, allowing for infinite horizontal scalability of agricultural commodities without modifying base logic.
* **The Observer Pattern (Event-Driven):** Implements an asynchronous event watcher (`QualityMonitor`) that subscribes to cargo batches, firing critical systemic alerts when quality drops below viable thresholds.

### 3. Enterprise Integrations
* **Live API Telemetry:** Integrates `urllib` to ping the Open-Meteo REST API, dynamically injecting live satellite weather data into the thermodynamic decay formulas based on the origin city's coordinates.
* **Geospatial Mapping:** Utilizes `PyDeck` (WebGL) to render real-time interactive 2D transit navigation lines between origin and destination markets.
* **Data Auditing:** Uses `pandas` to compile simulation state-tracking into exportable time-series CSV reports for financial ERP systems.

## 🛠️ Installation & Execution

This project is built with a strictly decoupled architecture (Backend OOP Engine + Frontend Streamlit View).

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/project-agrata.git](https://github.com/yourusername/project-agrata.git)
   cd project-agrata

2. **Install Dependencies:**
   ```bash
   pip install streamlit pandas pydeck

3. **Launch the interactive dashboard:**
   ```bash
   streamlit run frontend/app.py

📈 Future Roadmap (Version 2.0)
•**Predictive ML Integration:** Swap out current mathematical heuristics for a trained machine learning model to predict shelf-life and market demand dynamically.

•**IoT Sensor Hooks:** Replace Open-Meteo API data with live payload feeds from in-transit BLE/LoRa refrigeration sensors.

**Architected and Developed by Abhinav Gupta & Team.**