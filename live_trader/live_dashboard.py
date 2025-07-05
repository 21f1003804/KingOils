import streamlit as st
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
from data_utils import load_position_data, format_timestamp
from config import exchange_symbol_token_map

# === Page Config ===
st.set_page_config(page_title="Live Trading Dashboard", layout="wide")
st.title("📈 Real-Time Position Monitor")

# === Settings ===
REFRESH_INTERVAL = 10  # seconds
st_autorefresh(interval=REFRESH_INTERVAL * 1000, key="dash_refresh")

# === Provided mapping ===

# === Reverse map ===
token_to_display_name = {}
for exchange, symbol_dict in exchange_symbol_token_map.items():
    for symbol, token in symbol_dict.items():
        token_to_display_name[str(token)] = f"{symbol} ({exchange})"

# === Dashboard Layout ===
positions = load_position_data()

if not positions:
    st.warning("⏳ Waiting for position data...")
    st.stop()

tokens = list(positions.keys())
selected_token = st.sidebar.selectbox(
    "Select Instrument",
    tokens,
    format_func=lambda t: f"{token_to_display_name.get(t, 'Unknown')} [{t}]"
)

data = positions.get(selected_token, {})

if not data:
    st.error(f"No position data for token {selected_token}")
    st.stop()

# === Position Overview ===
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Entry Price", f"₹{data.get('entry_price', 'N/A')}")
with col2:
    st.metric("Current Price", f"₹{data.get('current_price', 'N/A')}")
with col3:
    profit = data.get('profit', 0)
    st.metric("Profit/Loss", f"₹{profit}", delta=f"{profit/100:.2f}%" if profit else None)

st.divider()

# === Historical Charts ===
def render_timeseries(title, values):
    if not values:
        return
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=values, 
        mode="lines+markers",
        name=title,
        line=dict(width=3)
    ))
    fig.update_layout(
        title=title,
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

render_timeseries("Supertrend History", data.get("supertrend_history"))
render_timeseries("ATR History", data.get("atr_history"))
render_timeseries("Profit History", data.get("profit_history"))

# === Position Metadata ===
with st.expander("Position Details"):
    st.write(f"**Entry Time:** {format_timestamp(data.get('entry_time'))}")
    st.write(f"**Price Source:** {data.get('price_source')}")
    st.write(f"**Trailing SL:** {data.get('trailing_sl')}")
    st.write(f"**Stop Hits:** {data.get('stop_hit_count', 0)}")
    st.write(f"**Direction Reversals:** {data.get('direction_reversed_count', 0)}")
    st.write(f"**Min Hold Met:** {data.get('min_hold_met_count', 0)}")

st.caption(f"Last updated: {format_timestamp(data.get('last_updated'))}")