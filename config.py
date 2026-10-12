"""
System Configuration, Dynamic Universe Ingestion, Scoring Weights, and Thresholds.
"""

import io
import requests
import pandas as pd

# Scoring Weights for the Composite Brain (Sums to 1.0)
WEIGHTS = {
    "FUNDAMENTAL_VALUE": 0.25,
    "TECHNICAL_CYCLE": 0.25,
    "CATALYST_ORDERBOOK": 0.25,
    "INSTITUTIONAL_FLOW": 0.25,
}

# Valuation, Solvency & Safety Thresholds
THRESHOLDS = {
    "MAX_PROMOTER_PLEDGE_PCT": 5.0,     # Maximum allowed promoter share pledge %
    "MIN_PIOTROSKI_SCORE": 6,          # 6 to 9 represents strong financial health
    "MAX_DEBT_TO_EQUITY": 1.5,          # Leverage cap
    "MAX_PEG_RATIO": 1.8,               # Growth at reasonable price threshold
    "RSI_OVERSOLD": 45.0,               # Reversal entry threshold
    "MIN_CYCLE_CONFIDENCE": 0.60,       # Minimum FFT cycle amplitude confidence
    "MIN_DAILY_TURNOVER_CR": 0.75       # Minimum ₹75 Lakhs average daily turnover
}

# Browser Headers for Direct Exchange and News Requests
HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

def get_expanded_nse_universe() -> list:
    """
    Downloads Nifty 500 and Nifty Microcap 250 constituent lists from official indices
    to scan large, mid, small, and high-growth micro-cap companies.
    """
    urls = [
        "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
        "https://archives.nseindia.com/content/indices/ind_niftymicrocap250_list.csv"
    ]
    all_symbols = set()
    
    for url in urls:
        try:
            res = requests.get(url, headers=HTTP_HEADERS, timeout=8)
            if res.status_code == 200:
                df = pd.read_csv(io.StringIO(res.text))
                if "Symbol" in df.columns:
                    for sym in df["Symbol"].dropna():
                        clean_sym = str(sym).strip().upper()
                        # Exclude delisted / merged legacy tickers
                        if clean_sym not in ["TATAMOTORS", "HDFC"]:
                            all_symbols.add(f"{clean_sym}.NS")
        except Exception:
            continue
            
    if len(all_symbols) >= 50:
        return sorted(list(all_symbols))
        
    # High-liquidity fallback universe if network request is blocked
    return [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "TMPV.NS", "SBIN.NS",
        "ICICIBANK.NS", "INFY.NS", "TITAN.NS", "ITC.NS", "BAJFINANCE.NS",
        "LT.NS", "HAL.NS", "BEL.NS", "BHEL.NS", "COALINDIA.NS", "NTPC.NS",
        "BHARTIARTL.NS", "ADANIPORTS.NS", "TATASTEEL.NS", "KOTAKBANK.NS",
        "MAZDOCK.NS", "COCHINSHIP.NS", "KAYNES.NS", "KPITTECH.NS", "SUZLON.NS"
    ]

# Loaded dynamically at startup
NSE_UNIVERSE = get_expanded_nse_universe()