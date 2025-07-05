api_key = "3cjan03ksbhpkvdi"
api_secret = "9iewjt8dhbecxx7muzeqjehyngh2vrva"
login_url = "https://kite.zerodha.com/connect/login?api_key=3cjan03ksbhpkvdi&v=3"
access_token = "5CtALk9NGRAoFZtzcKx771a9b3t6esFv"

TIMESCALE_DB_CONFIG = {
    "user": "postgres",
    "password": "1111",
    "database": "postgres",
    "host": "localhost",
    "port": 5432,
}

exchange_symbol_token_map = {
    'MCX': {
        'CRUDEOILM25JUNFUT': 114131463,
        'GOLDM25JULFUT': 116027143,
        'NATGASMINI25JUNFUT': 114244103,
        'SILVERMIC25JUNFUT':112787463
    },
    'NFO': {
        'CDSL25JUNFUT': 14553858,
        'MCX25JUNFUT': 14606594,
        'TATAPOWER25JUNFUT': 14653186,
        'IEX25JUNFUT':14585090
    },
    'NSE': {
        'CDSL': 5420545
    }
}