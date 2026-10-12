"""
High-Performance Asynchronous Data Fetcher for Prices, Financials, and NSE Filings.
"""

import asyncio
import aiohttp
import yfinance as yf
import pandas as pd
from typing import Dict, Any
from config import HTTP_HEADERS

class DataIngestionEngine:
    def __init__(self):
        self.headers = HTTP_HEADERS

    async def fetch_nse_announcements(self, session: aiohttp.ClientSession, symbol: str) -> list:
        """
        Fetches official corporate filings, board meeting outcomes, and order book
        disclosures directly from NSE corporate announcement endpoints.
        """
        clean_symbol = symbol.replace(".NS", "").replace(".BO", "")
        url = f"https://www.nseindia.com/api/corporate-announcements?index=equities&symbol={clean_symbol}"
        
        try:
            async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=4)) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("rows", [])
        except Exception:
            pass
        return []

    def get_market_history_batch(self, tickers: list, period: str = "2y") -> Dict[str, pd.DataFrame]:
        """
        Downloads multi-year vectorized OHLCV price histories in a single multi-threaded batch.
        """
        data = yf.download(
            tickers=tickers,
            period=period,
            interval="1d",
            group_by="ticker",
            threads=True,
            progress=False
        )
        result = {}
        for t in tickers:
            try:
                df = data[t].dropna() if len(tickers) > 1 else data.dropna()
                if not df.empty and len(df) > 80:
                    result[t] = df
            except Exception:
                continue
        return result

    def get_financial_statements(self, ticker: str) -> Dict[str, Any]:
        """
        Extracts balance sheets, income statements, cash flow, and institutional holdings.
        """
        try:
            stock = yf.Ticker(ticker)
            return {
                "info": stock.info or {},
                "financials": stock.financials,
                "balance_sheet": stock.balance_sheet,
                "cashflow": stock.cashflow,
                "major_holders": stock.major_holders,
                "institutional_holders": stock.institutional_holders
            }
        except Exception:
            return {}