import asyncio
import logging
from kiteconnect import KiteConnect, KiteTicker
from config import api_key, api_secret, access_token, exchange_symbol_token_map
from instrument_manager import instrument_data, initialize_all_instruments
from data_ingestion.tick_data import start_tick_data
from data_ingestion.intraday_data import update_intraday_data
from data_ingestion.daily_data import fetch_daily_data
from computation.indicators import global_monitor_intraday_indicators, global_monitor_daily_indicators
from decision.monitoring import monitor_instrument_signals
# === ADDED IMPORTS ===
import os
import json
import pandas as pd
import datetime
import numpy as np
# =====================

# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.WARNING)

print("API Key:", api_key)
print("API Secret:", api_secret)
print("Access Token:", access_token)

# Initialize Kite connection
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)
kws = KiteTicker(api_key, access_token)

# Initialize instruments
initialize_all_instruments(exchange_symbol_token_map)

# Global task variable
task = None

# Global run identifier
RUN_ID = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# === OPTIMIZED DATA SAVING FUNCTIONS ===
def json_safe(obj):
    """Robust JSON-safe conversion with numpy support"""
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif isinstance(obj, (list, tuple)):
        return [json_safe(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    else:
        return obj

async def save_position_snapshot():
    """Update position file for current run"""
    os.makedirs("./data/position_snapshots", exist_ok=True)
    target_file = f"./data/position_snapshots/positions_{RUN_ID}.json"
    
    while True:
        try:
            temp_file = f"./data/position_snapshots/temp_{RUN_ID}.json"
            
            snapshot = {}
            for token, data in instrument_data.items():
                pos_data = data.get('position_data', {})
                snapshot[token] = json_safe(pos_data)
            
            # Atomic update
            with open(temp_file, "w") as f:
                json.dump(snapshot, f, indent=2)
            os.replace(temp_file, target_file)
            
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ✅ Position snapshot updated")
            
        except Exception as e:
            print(f"⚠️ Error updating position snapshot: {e}")
        
        await asyncio.sleep(60)

async def export_signals():
    """Update signals file for current run"""
    os.makedirs("./data/signal_exports", exist_ok=True)
    target_file = f"./data/signal_exports/signals_{RUN_ID}.csv"
    
    while True:
        try:
            temp_file = f"./data/signal_exports/temp_{RUN_ID}.csv"
            
            all_signals = []
            for token, data in instrument_data.items():
                signals = data.get('signals')
                if isinstance(signals, pd.DataFrame) and not signals.empty:
                    df = signals.copy()
                    df['instrument_token'] = token
                    df['symbol'] = data.get('symbol', '')
                    all_signals.append(df)
            
            if all_signals:
                combined_df = pd.concat(all_signals)
                combined_df.to_csv(temp_file, index=False)
                os.replace(temp_file, target_file)
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ✅ Signals updated ({len(combined_df)} rows)")
            else:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ⚠️ No signals to update")
                
        except Exception as e:
            print(f"⚠️ Error updating signals: {e}")
        
        await asyncio.sleep(30)

# ===================================

async def main(kite, kws):
    """Main async entry point"""
    # Start tick data
    # tick_task = asyncio.create_task(start_tick_data(kws, instrument_data))
    
    # Start intraday and daily updates
    intraday_tasks = []
    daily_tasks = []
    monitoring_tasks = []
    
    for token in instrument_data:
        intraday_tasks.append(asyncio.create_task(update_intraday_data(kite, token, instrument_data)))
        daily_tasks.append(asyncio.create_task(fetch_daily_data(kite, token, instrument_data)))
        monitoring_tasks.append(asyncio.create_task(monitor_instrument_signals(kite, instrument_data, token)))
    
    # Add global indicator tasks
    indicator_tasks = [
        global_monitor_intraday_indicators(instrument_data),
        global_monitor_daily_indicators(instrument_data)
    ]
    
    # === ADDED DATA SAVING TASKS ===
    data_saving_tasks = [
        save_position_snapshot(),
        export_signals()
    ]
    # ==============================
    
    # Run all tasks concurrently
    await asyncio.gather(
        # tick_task, 
        *intraday_tasks, 
        *daily_tasks, 
        *monitoring_tasks,
        *indicator_tasks,
        *data_saving_tasks  # Added data saving tasks
    )

# ================================
# Task Control Functions
# ================================
def start_async_tasks(kite, kws):
    """Start all async tasks in the event loop"""
    global task
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Check if task is already running
    if task and not task.done():
        print("🔄 Monitoring already running")
        return
    
    # Create and start the main task
    task = loop.create_task(main(kite, kws))
    print(f"✅ Started monitoring for {len(instrument_data)} instruments")
    print("• Real-time signal monitoring")
    print("• Intraday & historical data collection")
    print("• Global indicator analysis")
    print("• Automated position/signal data exports")  # Added feature note

def stop_async_tasks():
    """Safely stop all running tasks"""
    global task
    if task and not task.done():
        task.cancel()
        print("🛑 Stopped all monitoring tasks")
        task = None
    else:
        print("⚠️ No active tasks to stop")

if __name__ == "__main__":
    start_async_tasks(kite, kws)
    # trading_loop()
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        stop_async_tasks()