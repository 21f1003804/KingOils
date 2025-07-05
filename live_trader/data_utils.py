import os
import glob
import json
import pandas as pd
from datetime import datetime
import time

def safe_json_load(path):
    """Robust JSON loading with retry mechanism"""
    for _ in range(3):  # Retry up to 3 times
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️ JSON decode error, retrying: {path}")
            time.sleep(0.1)  # Short delay before retry
    return {}  # Return empty on failure

def get_latest_position_file():
    """Get most recent position snapshot"""
    files = glob.glob("./data/position_snapshots/positions_*.json")
    if not files:
        return None
    return max(files, key=os.path.getctime)

def get_latest_signals_file():
    """Get most recent signals export"""
    files = glob.glob("./data/signal_exports/signals_*.csv")
    if not files:
        return None
    return max(files, key=os.path.getctime)

def load_position_data():
    """Safely load position data"""
    file_path = get_latest_position_file()
    if not file_path:
        return {}
    return safe_json_load(file_path)

def load_signals_data():
    """Load signals from latest CSV"""
    file_path = get_latest_signals_file()
    if not file_path:
        return pd.DataFrame()
    return pd.read_csv(file_path)

def format_timestamp(ts_str):
    """Convert ISO timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(ts_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return ts_str