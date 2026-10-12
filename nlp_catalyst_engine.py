"""
Corporate Disclosure Mining, Order Book Intelligence, and Institutional Accumulation NLP.
"""

import re
import urllib.parse
import feedparser
from typing import List, Dict, Any, Tuple

class NLPCatalystEngine:
    
    PATTERNS = {
        "ORDER_BOOK_WIN": [
            r"bagged order", r"contract win", r"secures order worth", 
            r"lowest bidder", r"l1 bidder", r"awarded contract", r"crore order",
            r"commercial order", r"procurement order", r"defence order", r"supply contract"
        ],
        "FII_INSTITUTIONAL_BUY": [
            r"fii stake", r"fpi buy", r"foreign investor", r"block deal",
            r"bulk deal", r"morgan stanley", r"vanguard", r"blackrock",
            r"stake acquisition", r"institutional inflow", r"promoter buying"
        ],
        "EARNINGS_CATALYST": [
            r"pat surges", r"ebitda grows", r"quarterly profit rises", 
            r"margin expansion", r"guidance upgrade", r"record quarterly revenue",
            r"net profit jumps", r"all-time high profit"
        ]
    }

    @staticmethod
    def parse_catalysts(symbol: str, exchange_filings: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """
        Scans both official NSE exchange filings and financial news RSS
        to capture contract wins, FII purchases, and pre-earnings margin surges.
        """
        detected_catalysts = []
        score = 30.0
        
        clean_symbol = symbol.replace(".NS", "").replace(".BO", "")
        encoded_query = urllib.parse.quote(f"{clean_symbol} stock order contract FII NSE profit")
        feed_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"

        text_corpus = []

        # 1. Ingest Official NSE Regulatory Disclosures
        for filing in exchange_filings[:10]:
            subject = filing.get("desc", "") or filing.get("attchmntText", "")
            if subject:
                text_corpus.append(str(subject).lower())

        # 2. Ingest Financial News Headlines
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:8]:
                text_corpus.append(entry.title.lower())
        except Exception:
            pass

        full_text = " ".join(text_corpus)

        # 3. Match Pattern Signals
        for category, regex_list in NLPCatalystEngine.PATTERNS.items():
            for regex in regex_list:
                if re.search(regex, full_text):
                    if category == "ORDER_BOOK_WIN" and "Massive Order Win" not in detected_catalysts:
                        detected_catalysts.append("Massive Order Win")
                        score += 25.0
                    elif category == "FII_INSTITUTIONAL_BUY" and "FII/DII Accumulation" not in detected_catalysts:
                        detected_catalysts.append("FII/DII Accumulation")
                        score += 25.0
                    elif category == "EARNINGS_CATALYST" and "Earnings Margin Surge" not in detected_catalysts:
                        detected_catalysts.append("Earnings Margin Surge")
                        score += 20.0

        catalyst_score = max(min(score, 100.0), 0.0)
        return catalyst_score, detected_catalysts