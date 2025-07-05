import pandas as pd
import datetime
import asyncio
import logging
from kiteconnect import KiteConnect

async def update_intraday_data(kite, token, instrument_data):
    """Pure data update function - no indicator computations"""
    data = instrument_data[token]
    while True:
        try:
            # Get current time in IST
            now = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(hours=5, minutes=30)
            to_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
            
            # Determine from_time
            if not data['intraday'].empty and 'date' in data['intraday'].columns:
                last_time = data['intraday']['date'].max()
                if isinstance(last_time, pd.Timestamp):
                    last_time = last_time.tz_convert(None)
                from_time = last_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                from_time = (now - datetime.timedelta(days=30)).replace(
                    hour=9, minute=0, second=0, microsecond=0
                ).strftime("%Y-%m-%d %H:%M:%S")
            
            # Fetch new data
            new_data = kite.historical_data(
                token, 
                from_date=from_time, 
                to_date=to_time_str, 
                interval="5minute"
            )
            new_df = pd.DataFrame(new_data)
            
            if not new_df.empty:
                if not data['intraday'].empty:
                    data['intraday'] = pd.concat([data['intraday'], new_df])
                    logging.info(f"Intraday new candle:{new_df.iloc[-1]}")
                    data['intraday'] = data['intraday'].drop_duplicates(subset=['date'], keep='last')
                else:
                    data['intraday'] = new_df
                
                data['intraday'] = data['intraday'].sort_values('date')
                data['intraday'] = data['intraday'].reset_index(drop=True)
                
                print(f"Intraday updated for {data['symbol']}: {len(data['intraday'])} records")
            
        except Exception as e:
            logging.error(f"Data update error for {data['symbol']}: {str(e)}")
        
        await asyncio.sleep(30)
