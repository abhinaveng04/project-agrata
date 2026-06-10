import sqlite3
import uuid
import pandas as pd

class EnterpriseDB:
    def __init__(self, db_name="agrata_v2.sqlite3"):
        self.db_name = db_name
        self._create_tables()

    def _get_connection(self):
        return sqlite3.connect(self.db_name)

    def _create_tables(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Table for persisting the Simulation Audit Logs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS supply_chain_runs (
                    run_id TEXT PRIMARY KEY,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    origin_city TEXT,
                    destination_city TEXT,
                    crop_type TEXT,
                    transport_type TEXT,
                    distance_km INTEGER,
                    final_quality REAL,
                    market_value REAL
                )
            ''')
            conn.commit()

    def log_run(self, origin, dest, crop, transport_type, distance, quality, value):
        run_id = str(uuid.uuid4())
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO supply_chain_runs 
                (run_id, origin_city, destination_city, crop_type, transport_type, distance_km, final_quality, market_value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (run_id, origin, dest, crop, transport_type, distance, quality, value))
            conn.commit()

    def get_all_runs(self):
        """Returns a Pandas DataFrame of all historical runs for Streamlit."""
        with self._get_connection() as conn:
            return pd.read_sql_query("SELECT * FROM supply_chain_runs ORDER BY timestamp DESC", conn)

# Initialize a singleton instance for the app to use
db = EnterpriseDB()