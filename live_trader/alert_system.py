import pandas as pd
import time
import hashlib
import os
import platform
import subprocess
import glob
from datetime import datetime

DATA_DIR = "./data/signal_exports/"
seen_hashes = set()
last_file_size = 0
last_mtime = 0
current_csv = None

print("🔍 Starting signal export watcher...")
print(f"📂 Monitoring directory: {DATA_DIR}")

def get_latest_csv():
    """Find the newest CSV file in signal_exports directory"""
    csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    if not csv_files:
        return None
    return max(csv_files, key=os.path.getmtime)

def row_hash(row):
    """Generate a unique hash for a row"""
    return hashlib.sha256(
        "|".join(str(x) for x in row).encode()
    ).hexdigest()

def play_alert():
    """Cross-platform alert sound"""
    if platform.system() == 'Windows':
        import winsound
        winsound.Beep(1000, 1000)
    elif platform.system() == 'Darwin':
        subprocess.run(['afplay', '/System/Library/Sounds/Ping.aiff'])
    else:
        print('\a')  # Terminal bell
        subprocess.run(['spd-say', 'New trading signal'])

def clear_screen():
    """Clear terminal screen cross-platform"""
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

def format_alert(row):
    """Create visual alert message"""
    action = row.get('signal', row.get('action', 'UNKNOWN')).upper()
    color_code = ""
    reset_code = ""
    
    # Add color if supported (not Windows)
    if platform.system() != 'Windows':
        color_code = "\033[93m" if "BUY" in action else "\033[91m"
        reset_code = "\033[0m"
    
    return (
        f"{color_code}🚨 NEW SIGNAL AT {datetime.now().strftime('%H:%M:%S')}{reset_code}\n"
        f"Symbol: {row.get('symbol', 'N/A')}\n"
        f"Action: {color_code}{action}{reset_code}\n"
        f"position: {row.get('position', 'N/A')}\n"
        f"price: {row.get('price', 'N/A')}\n"
        f"Confidence: {row.get('confidence', 0.0)*100:.1f}%\n"
        f"Timestamp: {row.get('timestamp', 'N/A')}\n"
        f"Reason: {row.get('reason', 'No reason provided')}"
    )

while True:
    try:
        # Find latest CSV file in signal_exports
        latest_csv = get_latest_csv()
        
        if not latest_csv:
            print(f"⚠️ No CSV files found in {DATA_DIR}")
            time.sleep(5)
            continue
            
        # Switch to new file if detected
        if current_csv != latest_csv:
            print(f"📁 New file detected: {os.path.basename(latest_csv)}")
            seen_hashes = set()  # Reset seen hashes for new file
            last_file_size = 0
            last_mtime = 0
            current_csv = latest_csv
        
        # Check if file has changed
        current_size = os.path.getsize(current_csv)
        current_mtime = os.path.getmtime(current_csv)
        
        # Skip processing if file hasn't changed
        if current_size == last_file_size and current_mtime == last_mtime:
            time.sleep(5)
            continue
            
        last_file_size = current_size
        last_mtime = current_mtime
        
        # Read CSV with error handling
        try:
            df = pd.read_csv(current_csv)
        except pd.errors.EmptyDataError:
            print(f"⚠️ CSV file is empty: {os.path.basename(current_csv)}")
            time.sleep(5)
            continue
        except pd.errors.ParserError:
            print(f"⚠️ Error parsing CSV: {os.path.basename(current_csv)}")
            time.sleep(5)
            continue
            
        # Skip if no data
        if df.empty:
            time.sleep(5)
            continue
            
        # Compute hashes and find new rows
        current_hashes = set(df.apply(row_hash, axis=1))
        new_hashes = current_hashes - seen_hashes
        
        if new_hashes:
            clear_screen()
            new_rows = df[df.apply(lambda row: row_hash(row) in new_hashes, axis=1)]
            
            print(f"📁 Active file: {os.path.basename(current_csv)}")
            print(f"🚨 {len(new_rows)} NEW SIGNAL(S) DETECTED")
            print("="*50)
            for _, row in new_rows.iterrows():
                print("\n" + format_alert(row))
                print("-"*50)
            print("="*50)
                
            play_alert()
            seen_hashes.update(new_hashes)
            
        time.sleep(3)  # Slightly faster polling

    except Exception as e:
        print(f"[CRITICAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        time.sleep(10)

        