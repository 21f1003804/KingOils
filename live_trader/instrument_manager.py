import pandas as pd
import datetime

instrument_data = {}

def init_instrument_data(token, symbol, intraday_df=None):
    """Initialize new instrument with consistent structure"""
    instrument_data[token] = {
        'symbol': symbol,
        'tick': pd.DataFrame(),
        'intraday': intraday_df if intraday_df is not None else pd.DataFrame(),
        'daily': pd.DataFrame(),
        'signals': pd.DataFrame(columns=['timestamp', 'action', 'position', 'price', 'price_source', 'exit_reason']),
        'position': None,
        'current_position': None,
        'position_data': {},
        'last_exit_time': None,
        'last_exit_position': None,
        'was_premature_exit': False,
        'checksums': {'intraday': None, 'daily': None}
    }

def initialize_all_instruments(exchange_map):
    """Initialize all instruments from config"""
    for exchange in exchange_map.keys():
        for symbol, token in exchange_map[exchange].items():
            modified_symbol = f"{exchange}:{symbol}"
            init_instrument_data(token=token, symbol=modified_symbol)
