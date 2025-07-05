import pandas as pd
import numpy as np
import hashlib
import logging
import asyncio



def compute_checksum(df):
    """Compute checksum for a DataFrame"""
    return hashlib.md5(pd.util.hash_pandas_object(df, index=True).values).hexdigest()

def compute_atr(df, period=14):
    """Calculate ATR for a given DataFrame"""
    df = df.copy()
    df['prev_close'] = df['close'].shift()
    df['tr'] = np.maximum(df['high'] - df['low'], 
                          np.maximum(abs(df['high'] - df['prev_close']), 
                                     abs(df['low'] - df['prev_close'])))
    atr = df['tr'].rolling(window=period).mean()
    return atr.iloc[-1]

def compute_supertrend(df, period=10, multiplier=3):
    """Supertrend calculation for a given DataFrame"""
    df = df.copy()
    # Original supertrend logic preserved
    df['hl2'] = (df['high'] + df['low']) / 2
    df['tr'] = np.maximum(
        df['high'] - df['low'],
        np.maximum(
            abs(df['high'] - df['close'].shift(1)),
            abs(df['low'] - df['close'].shift(1))
        )
    )
    
    alpha = 1 / period
    df['atr'] = np.nan
    sma_initial = df['tr'].rolling(period, min_periods=1).mean()
    df.loc[period-1, 'atr'] = sma_initial.iloc[period-1]
    
    for i in range(period, len(df)):
        df.at[i, 'atr'] = alpha * df.at[i, 'tr'] + (1 - alpha) * df.at[i-1, 'atr']
    
    df['upper_band'] = df['hl2'] + multiplier * df['atr']
    df['lower_band'] = df['hl2'] - multiplier * df['atr']
    
    start_idx = period - 1
    df['final_upper_band'] = np.nan
    df['final_lower_band'] = np.nan
    df.loc[start_idx, ['final_upper_band', 'final_lower_band']] = df.loc[start_idx, ['upper_band', 'lower_band']].values
    
    for i in range(start_idx + 1, len(df)):
        current_upper = df.at[i, 'upper_band']
        prev_upper = df.at[i-1, 'final_upper_band']
        prev_close = df.at[i-1, 'close']
        df.at[i, 'final_upper_band'] = current_upper if (current_upper < prev_upper) or (prev_close > prev_upper) else prev_upper
        
        current_lower = df.at[i, 'lower_band']
        prev_lower = df.at[i-1, 'final_lower_band']
        df.at[i, 'final_lower_band'] = current_lower if (current_lower > prev_lower) or (prev_close < prev_lower) else prev_lower
    
    df['direction'] = 1
    df['supertrend'] = df['final_upper_band']
    
    for i in range(start_idx + 1, len(df)):
        current_close = df.at[i, 'close']
        prev_supertrend = df.at[i-1, 'supertrend']
        
        if current_close > df.at[i, 'final_upper_band']:
            df.at[i, 'direction'] = -1
            df.at[i, 'supertrend'] = df.at[i, 'final_lower_band']
        elif current_close < df.at[i, 'final_lower_band']:
            df.at[i, 'direction'] = 1
            df.at[i, 'supertrend'] = df.at[i, 'final_upper_band']
        else:
            df.at[i, 'direction'] = df.at[i-1, 'direction']
            df.at[i, 'supertrend'] = df.at[i, 'final_lower_band'] if df.at[i, 'direction'] == -1 else df.at[i, 'final_upper_band']
    
    return df

def compute_fisher_transform(df, length=10):
    """Fisher Transform for a given DataFrame"""
    df = df.copy()
    df['hl2'] = (df['high'] + df['low']) / 2
    df['high_hl2'] = df['hl2'].rolling(length, min_periods=1).max()
    df['low_hl2'] = df['hl2'].rolling(length, min_periods=1).min()
    df['value'] = 0.0
    df['fisher'] = 0.0
    df['trigger'] = np.nan

    for i in range(1, len(df)):
        denom = df.at[i, 'high_hl2'] - df.at[i, 'low_hl2'] or 1e-9
        current_val = 0.66 * ((df.at[i, 'hl2'] - df.at[i, 'low_hl2']) / denom - 0.5) + 0.67 * df.at[i-1, 'value']
        df.at[i, 'value'] = min(max(current_val, -0.99), 0.999)

    for i in range(1, len(df)):
        prev_fisher = df.at[i-1, 'fisher']
        current_val = df.at[i, 'value']
        fisher_val = 0.5 * np.log((1 + current_val) / (1 - current_val)) + 0.5 * prev_fisher
        df.at[i, 'fisher'] = fisher_val

    df['trigger'] = df['fisher'].shift(1)
    return df

def compute_indicators_for_instrument(instrument_data, token, name):
    """Compute indicators for specific instrument and data type"""
    data = instrument_data[token]
    if name == 'intraday':
        if not data['intraday'].empty:
            data['intraday'] = compute_fisher_transform(data['intraday'])
            data['intraday'] = compute_supertrend(data['intraday'])
    elif name == 'daily':
        if not data['daily'].empty:
            data['daily'] = compute_supertrend(data['daily'])

async def global_monitor_intraday_indicators(instrument_data, interval=5):
    """Monitor intraday data changes for all instruments and compute indicators"""
    while True:
        for token in instrument_data:
            data = instrument_data[token]
            if data['intraday'] is None or data['intraday'].empty:
                continue
                
            current_checksum = compute_checksum(data['intraday'])
            if current_checksum != data['checksums']['intraday']:
                print(f"Intraday data changed for {data['symbol']}. Computing indicators...")
                compute_indicators_for_instrument(instrument_data, token, 'intraday')
                data['checksums']['intraday'] = current_checksum
                
        await asyncio.sleep(interval)

async def global_monitor_daily_indicators(instrument_data, interval=5):
    """Monitor daily data changes for all instruments and compute indicators"""
    while True:
        for token in instrument_data:
            data = instrument_data[token]
            if data['daily'] is None or data['daily'].empty:
                continue
                
            current_checksum = compute_checksum(data['daily'])
            if current_checksum != data['checksums']['daily']:
                print(f"Daily data changed for {data['symbol']}. Computing indicators...")
                compute_indicators_for_instrument(instrument_data, token, 'daily')
                data['checksums']['daily'] = current_checksum
                
        await asyncio.sleep(interval)
