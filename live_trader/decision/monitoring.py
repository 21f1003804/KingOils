import datetime
import logging
import asyncio
import pandas as pd
from .signals import get_live_price_data, log_signal, minutes_since
from computation.indicators import compute_atr

# Global constants
MIN_HOLD_DURATION = datetime.timedelta(minutes=5)
EXIT_BUFFER = 100
REENTRY_COST = 300
REENTRY_WINDOW = datetime.timedelta(minutes=15)
VOLATILITY_MULTIPLIER = 0.5

async def handle_position_logic(kite, instrument_data, token):
    data = instrument_data[token]
    symbol = data['symbol']

    if data['intraday'] is None or len(data['intraday']) < 15:
        return

    row = data['intraday'].iloc[-1]
    prev_row = data['intraday'].iloc[-2]
    now = datetime.datetime.now()

    live_data = get_live_price_data(kite, symbol)
    if not live_data:
        return

    ltp = live_data['ltp']
    position = data['position']
    position_data = data['position_data']
    last_exit_time = data['last_exit_time']
    last_exit_position = data['last_exit_position']
    was_premature_exit = data['was_premature_exit']
    reentry_triggered = False
    trigger_price = ltp  # Use last close price as trigger

    # --- Re-entry Logic ---
    if was_premature_exit and minutes_since(last_exit_time) <= REENTRY_WINDOW.total_seconds() / 60:
        try:
            exit_signals = data['signals'][data['signals']['action'] == 'EXIT']
            if not exit_signals.empty:
                prior_exit_price = exit_signals.iloc[-1]['price']
                price_diff = abs(ltp - prior_exit_price)

                if last_exit_position == 'LONG':
                    condition = ((row['direction'] == -1 and prev_row['direction'] == 1) or 
                                 trigger_price > prev_row['supertrend'])
                    if condition and price_diff <= REENTRY_COST:
                        position = 'LONG'
                        position_data = {
                            'entry_price': ltp,
                            'entry_time': now,
                            'highest_price': row['high'],
                            'supertrend_history': [row['supertrend']],
                            'atr_history': [],
                            'profit_history': [],
                            'trailing_sl_history': [],
                            'stop_hit_history': [],
                            'direction_reversed_history': [],
                            'min_hold_met_history': [],
                            'price_source': 'reentry_ltp'
                        }
                        log_signal(instrument_data, token, 'REENTRY', position, ltp, 'ltp', None)
                        reentry_triggered = True
                        was_premature_exit = False

                elif last_exit_position == 'SHORT':
                    condition = ((row['direction'] == 1 and prev_row['direction'] == -1) or 
                                 trigger_price < prev_row['supertrend'])
                    if condition and price_diff <= REENTRY_COST:
                        position = 'SHORT'
                        position_data = {
                            'entry_price': ltp,
                            'entry_time': now,
                            'lowest_price': row['low'],
                            'supertrend_history': [row['supertrend']],
                            'atr_history': [],
                            'profit_history': [],
                            'trailing_sl_history': [],
                            'stop_hit_history': [],
                            'direction_reversed_history': [],
                            'min_hold_met_history': [],
                            'price_source': 'reentry_ltp'
                        }
                        log_signal(instrument_data, token, 'REENTRY', position, ltp, 'ltp', None)
                        reentry_triggered = True
                        was_premature_exit = False
        except Exception as e:
            logging.error(f"Re-entry error for {symbol}: {e}")

    # --- Entry Logic ---
    if not position and not reentry_triggered:
        try:
            entry_price = None
            if 'direction' not in row or 'direction' not in prev_row:
                logging.warning(f"Missing 'direction' column for {symbol}")
                return

            if (row['direction'] == -1 and prev_row['direction'] == 1) or trigger_price > prev_row['supertrend']:
                entry_price = max(live_data['best_ask'], prev_row['supertrend'], ltp)
                position = 'LONG'
                position_data = {
                    'entry_price': entry_price,
                    'entry_time': now,
                    'highest_price': row['high'],
                    'supertrend_history': [row['supertrend']],
                    'atr_history': [],
                    'profit_history': [],
                    'trailing_sl_history': [],
                    'stop_hit_history': [],
                    'direction_reversed_history': [],
                    'min_hold_met_history': [],
                    'price_source': 'best_ask' if live_data['best_ask'] == entry_price else 'supertrend' if prev_row['supertrend'] == entry_price else 'ltp'
                }
            elif (row['direction'] == 1 and prev_row['direction'] == -1) or trigger_price < prev_row['supertrend']:
                entry_price = min(live_data['best_bid'], prev_row['supertrend'], ltp)
                position = 'SHORT'
                position_data = {
                    'entry_price': entry_price,
                    'entry_time': now,
                    'lowest_price': row['low'],
                    'supertrend_history': [row['supertrend']],
                    'atr_history': [],
                    'profit_history': [],
                    'trailing_sl_history': [],
                    'stop_hit_history': [],
                    'direction_reversed_history': [],
                    'min_hold_met_history': [],
                    'price_source': 'best_bid' if live_data['best_bid'] == entry_price else 'supertrend' if prev_row['supertrend'] == entry_price else 'ltp'
                }

            if entry_price:
                # print('Entry',position, entry_price)
                log_signal(instrument_data, token, 'ENTRY', position, entry_price, position_data['price_source'], None)
        except Exception as e:
            logging.error(f"Entry error for {symbol}: {e}")

    # --- Exit Logic ---
    if position:
        exit_price = None
        reason = None

        try:
            atr = compute_atr(data['intraday'])

            if position == 'LONG':
                position_data['highest_price'] = max(position_data.get('highest_price', 0), row['high'])
                position_data['supertrend_history'].append(row['supertrend'])

                entry_price = position_data['entry_price']
                current_profit = trigger_price - entry_price
                atr_multiplier = 1.5 if current_profit < 2 * atr else 1

                # trailing_sl = position_data['highest_price'] - (atr * atr_multiplier) - EXIT_BUFFER
                trailing_sl = prev_row['supertrend'] - EXIT_BUFFER
                stop_hit = trigger_price < trailing_sl

                direction_reversed = (
                    (row['direction'] == 1 and prev_row['direction'] == -1) or 
                    (trigger_price < prev_row['supertrend'])
                )

            elif position == 'SHORT':
                position_data['lowest_price'] = min(position_data.get('lowest_price', float('inf')), row['low'])
                position_data['supertrend_history'].append(row['supertrend'])

                entry_price = position_data['entry_price']
                current_profit = entry_price - trigger_price
                atr_multiplier = 1.5 if current_profit < 2 * atr else 0.75

                # trailing_sl = position_data['lowest_price'] + (atr * atr_multiplier) + EXIT_BUFFER
                trailing_sl = prev_row['supertrend'] + EXIT_BUFFER
                stop_hit = trigger_price > trailing_sl

                direction_reversed = (
                    (row['direction'] == -1 and prev_row['direction'] == 1) or 
                    (trigger_price > prev_row['supertrend'])
                )

            hold_duration = now - position_data['entry_time']
            min_hold_met = hold_duration >= MIN_HOLD_DURATION

            # Append tracking values
            position_data['atr_history'].append(atr)
            position_data['profit_history'].append(current_profit)
            position_data['trailing_sl_history'].append(trailing_sl)
            position_data['stop_hit_history'].append(stop_hit)
            position_data['direction_reversed_history'].append(direction_reversed)
            position_data['min_hold_met_history'].append(min_hold_met)

            # if (stop_hit or direction_reversed) and min_hold_met:
            if (stop_hit) and min_hold_met:

                exit_price = live_data['best_bid'] if position == 'LONG' else live_data['best_ask']
                reason = 'STOPLOSS' if stop_hit else 'DIRECTION_REVERSAL'

        except Exception as e:
            logging.error(f"Exit error for {symbol}: {e}")

        if exit_price:
            # print('EXIT',position, entry_price)
            log_signal(instrument_data, token, 'EXIT', position, exit_price, 'live', reason)
            data['last_exit_time'] = now
            data['last_exit_position'] = position
            data['was_premature_exit'] = (reason == 'STOPLOSS')
            position = None
            position_data = {}

    data['position'] = position
    data['position_data'] = position_data
    data['was_premature_exit'] = was_premature_exit
    data['current_position'] = position


async def monitor_instrument_signals(kite, instrument_data, token):
    """Continuous signal monitoring with initial delay for setup"""
    # Initial wait for system initialization (120 seconds)
    logging.info(f"🕒 Delaying initial monitoring for {token} (120s for setup)")
    await asyncio.sleep(100)  
    
    logging.info(f"🚀 Starting continuous monitoring for {token}")
    while True:
        try:
            await handle_position_logic(kite, instrument_data, token)
            await asyncio.sleep(10)  # Regular check interval
        except Exception as e:
            logging.error(f"Signal monitoring error for {token}: {str(e)}")
            await asyncio.sleep(30)  # Backoff on error
