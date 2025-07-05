import datetime
import logging
import pandas as pd
from kiteconnect import KiteConnect

def get_live_price_data(kite, symbol):
    """Get real-time market data with error handling"""
    try:
        data = kite.quote(symbol)[symbol]
        return {
            'ltp': data['last_price'],
            'best_ask': data['depth']['sell'][0]['price'],
            'best_bid': data['depth']['buy'][0]['price'],
            'volume': data['volume']
        }
    except Exception as e:
        logging.error(f"Price data error for {symbol}: {str(e)}")
        return None

def log_signal(instrument_data, token, action, position, price, source, reason):
    """Log trading signal to instrument's signal history"""
    now = datetime.datetime.now()
    new_signal = pd.DataFrame([{
        'timestamp': now,
        'action': action,
        'position': position.upper(),
        'price': price,
        'price_source': source,
        'exit_reason': reason
    }])
    
    # Append to token's signals (not signals_df)
    data = instrument_data[token]
    # data['signals'] = pd.concat([data['signals'], new_signal], ignore_index=True)

    # Only concatenate if new_signal is not empty
    if not new_signal.empty:
        if data['signals'].empty:
            # If the current signals DataFrame is empty, then we can just assign the new_signal
            data['signals'] = new_signal
        else:
            # Otherwise, concatenate
            data['signals'] = pd.concat([data['signals'], new_signal], ignore_index=True)

    
    logging.info(f"{data['symbol']} {position.upper()} {action} @ {price} ({reason})")

def minutes_since(past_time):
    """Calculate minutes elapsed since given time"""
    if past_time is None:
        return float('inf')
    return (datetime.datetime.now() - past_time).total_seconds() / 60
