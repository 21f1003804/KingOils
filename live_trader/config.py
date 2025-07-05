
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

exchange_symbol_token_map = {
    'MCX': {
        # 'CRUDEOILM25JUNFUT': 114131463,
        'GOLDM25JULFUT': 116027143,
        'NATGASMINI25JUNFUT': 114244103,
        'SILVERMIC25JUNFUT':112787463
    },
    'NFO': {
        # 'CDSL25JUNFUT': 14553858,
        'MCX25JUNFUT': 14606594,
        # 'TATAPOWER25JUNFUT': 14653186,
        # 'IEX25JUNFUT':14585090
    },
    'NSE': {
        'CDSL': 5420545,
        'BSE':5013761,
        'JSWENERGY':4574465,
        
        'INDHOTEL':387073,
        'TATAPOWER':877057,
        'BEL':98049,
        'IEX':56321,
        # 'MCX':7982337,
        # 'SUZLON':3076609,
        # 'POLYCAB':2455041,
        # 'ALKEM':2995969,
        # 'DALBHARAT':2067201,
        # 'HAL':589569,
        # 'ITCHOTELS':7488257,
        # 'JSL':2876417,
        # 'KPITTECH':2478849,
        # 'LAURUSLABS':4923905,
        # 'PAGEIND':3689729,
        # 'PCJEWELLER':7455745,
        # 'QPOWER':7606017,
        # 'RPOWER':3906305,
        # 'TATACHEM':871681,
        # 'TRENT':502785,
        # 'VEDL':784129,
        # 'VOLTAS':951809
    }
}