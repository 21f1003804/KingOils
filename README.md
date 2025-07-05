# 🧠 Medium-Frequency Trading Engine (MFT)

This project is a medium-frequency trading engine designed for real-time tick/intraday data ingestion, strategy computation, automated execution, and live dashboard visualization. It supports live trading using Kite Connect and stores trade-related data in memory.

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone (https://github.com/21f1003804/KingOils.git)
cd KingOils
```

### 2. Install Requirements

```bash
pip install -r requirements.txt
```

---

### 3. Set up Configuration

Create a `config.py` file in the root directory with the following content:

```python
# config.py

api_key = "xxxxxxxx"
api_secret = "xxxxxxxx"
login_url = "xxxxxxxx"
access_token = "xxxxxxxx"

TIMESCALE_DB_CONFIG = {
    "user": "postgres",
    "password": "xxxxxxxx",
    "database": "xxxxxxxx",
    "host": "localhost",
    "port": 5432,
}
```

---

### 4. Run the Application

To start the trading engine and launch the live dashboard:

```bash
python main.py
```

This will:

- Begin real-time data ingestion and computation  
- Execute trades based on predefined strategy and risk rules  
- Store data in memory  
- Launch a live **Streamlit** dashboard hosted locally

---

## 📊 Dashboard Access

Once running, the Streamlit dashboard will be available at:

```
http://localhost:8501
```

This dashboard shows real-time strategy signals, trade history, stop-loss levels, and performance metrics.

---
