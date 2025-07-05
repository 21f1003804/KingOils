import pandas as pd
import datetime
import asyncio
import logging
from kiteconnect import KiteConnect

async def fetch_daily_data(kite, token, instrument_data):
    """Fetch daily data for specific instrument"""
    data = instrument_data[token]
    while True:
        try:
            from_date = (datetime.datetime.now() - datetime.timedelta(days=50)).strftime("%Y-%m-%d")
            to_date = datetime.datetime.now().strftime("%Y-%m-%d")
            new_data = kite.historical_data(token, from_date=from_date, to_date=to_date, interval="day")
            data['daily'] = pd.DataFrame(new_data)
            print(f"Daily data updated for {data['symbol']}: {len(data['daily'])} records")
        except Exception as e:
            logging.error(f"Daily data error for {data['symbol']}: {str(e)}")
        
        await asyncio.sleep(86400)  # Update daily
