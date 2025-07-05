import pandas as pd
import asyncio
import logging
from kiteconnect import KiteTicker
from instrument_manager import instrument_data   # without the relative



def ticks_to_dataframe(ticks, token):
    """Process ticks into DataFrame for specific instrument"""
    data = {col: [] for col in [
        "tradable", "mode", "instrument_token", "last_price", 
        "last_traded_quantity", "average_traded_price", "volume_traded",
        "total_buy_quantity", "total_sell_quantity", "open", "high",
        "low", "close", "change", "last_trade_time", "oi", "oi_day_high",
        "oi_day_low", "exchange_timestamp", "depth_buy", "depth_sell"
    ]}
    
    for tick in ticks:
        if tick['instrument_token'] != token:
            continue
            
        for key in data.keys():
            if key == 'ohlc':
                ohlc = tick.get('ohlc', {})
                for ohlc_key in ['open', 'high', 'low', 'close']:
                    data[ohlc_key].append(ohlc.get(ohlc_key, 0))
            elif key == 'depth':
                depth = tick.get('depth', {"buy": [], "sell": []})
                data['depth_buy'].append(depth.get('buy', []))
                data['depth_sell'].append(depth.get('sell', []))
            else:
                data[key].append(tick.get(key, None))
    
    new_df = pd.DataFrame(data)
    existing_df = instrument_data[token]['tick']
    return pd.concat([existing_df, new_df], ignore_index=True) if not existing_df.empty else new_df

async def start_tick_data(kws, instrument_data):
    """Handle tick data for all instruments"""
    def on_ticks(ws, ticks):
        """Process incoming ticks"""
        for token in instrument_data:
            instrument_ticks = [t for t in ticks if t['instrument_token'] == token]
            if instrument_ticks:
                instrument_data[token]['tick'] = ticks_to_dataframe(instrument_ticks, token)
                print(f"Updated tick data for {instrument_data[token]['symbol']}")

    def on_connect(ws, response):
        """Subscribe to all tracked instruments"""
        tokens = list(instrument_data.keys())
        ws.subscribe(tokens)
        ws.set_mode(ws.MODE_FULL, tokens)
        print(f"Subscribed to {len(tokens)} instruments")

    kws.on_ticks = on_ticks
    kws.on_connect = on_connect
    kws.connect(threaded=True)

    while True:
        await asyncio.sleep(1)
