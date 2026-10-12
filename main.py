"""
main.py: Multi-Category Intelligence Reporter for Terminal & Dashboard.
"""

import asyncio
import aiohttp
import pandas as pd
from typing import Dict, Any, List

from config import NSE_UNIVERSE
from data_fetcher import DataIngestionEngine
from smallcap_growth_engine import SmallCapGrowthEngine
from fundamental_valuation_engine import FundamentalValuationEngine
from cyclical_pattern_engine import CyclicalPatternEngine
from nlp_catalyst_engine import NLPCatalystEngine
from composite_scoring_engine import CompositeScoringEngine
import io
import contextlib
import os
from emailer import send_email, format_html_report, wrap_html

def stage_1_vectorized_prefilter(hist_batch: Dict[str, pd.DataFrame]) -> List[str]:
    shortlist = []
    for ticker, df in hist_batch.items():
        if len(df) < 80 or not SmallCapGrowthEngine.verify_liquidity_and_circuits(df):
            continue
            
        close = df["Close"]
        curr_price = float(close.iloc[-1])
        ema_200 = float(close.ewm(span=200, adjust=False).mean().iloc[-1])
        
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        rsi = float((100 - (100 / (1 + rs))).iloc[-1])

        _, has_volume_surge = SmallCapGrowthEngine.detect_volume_catalyst(df)

        if (rsi <= 52.0 and curr_price >= (ema_200 * 0.90)) or has_volume_surge:
            shortlist.append(ticker)
            
    return shortlist

async def analyze_stock_pipeline(
    ticker: str, 
    hist_df: pd.DataFrame, 
    fetcher: DataIngestionEngine, 
    session: aiohttp.ClientSession
) -> Dict[str, Any]:
    try:
        curr_price = float(hist_df["Close"].iloc[-1])
        
        # 1. Technical & Cyclical Engine
        tech_score, est_recovery_days, target_price, tech_meta = (
            CyclicalPatternEngine.calculate_technical_confluence(hist_df)
        )
        _, has_volume_breakout = SmallCapGrowthEngine.detect_volume_catalyst(hist_df)

        # 2. Ingest Financials & Announcements
        fin_data = fetcher.get_financial_statements(ticker)
        announcements = await fetcher.fetch_nse_announcements(session, ticker)

        # 3. Fundamental Valuation Engine
        f_score = FundamentalValuationEngine.calculate_piotroski_f_score(fin_data)
        fund_score, fund_meta = FundamentalValuationEngine.evaluate_valuation_and_safety(
            fin_data.get("info", {}), f_score
        )

        # 4. News & Institutional NLP
        catalyst_score, detected_catalysts = NLPCatalystEngine.parse_catalysts(ticker, announcements)
        is_fii = "FII/DII Accumulation" in detected_catalysts
        inst_score = 80.0 if is_fii else 45.0

        # 5. Composite Score
        composite_score = CompositeScoringEngine.synthesize_score(
            fund_score, tech_score, catalyst_score, inst_score, has_volume_breakout
        )

        category = CompositeScoringEngine.categorize_opportunity(
            composite_score, detected_catalysts, f_score, has_volume_breakout
        )

        clean_symbol = ticker.replace(".NS", "")
        pe_val = fund_meta.get("PE_Ratio", 999.0)
        graham_val = fund_meta.get("Graham_Fair_Value", 0.0)

        return {
            "Stock": clean_symbol,
            "Current_Price": f"₹{curr_price:,.2f}",
            "Target_Sell": f"₹{target_price:,.2f}",
            "Hold_Days": f"{est_recovery_days}d",
            "Win_Prob": f"{int(composite_score)}%",
            "Piotroski": f"{f_score}/9",
            "RSI_14": tech_meta["RSI_14"],
            "P/E": pe_val,
            "Cycle_Length": f"{tech_meta['Dominant_Cycle_Days']} days",
            "Cycle_Conf": f"{int(tech_meta['Cycle_Confidence'] * 100)}%",
            "Graham_Value": f"₹{graham_val:,.2f}" if graham_val > 0 else "N/A",
            "Pledged%": f"{fund_meta.get('Pledged_Pct', 0)}%",
            "Catalysts": ", ".join(detected_catalysts) if detected_catalysts else "Technical Reversal",
            "Category": category,
            "Raw_Score": composite_score,
            "Raw_F_Score": f_score,
            "Raw_PE": float(pe_val) if pe_val != "N/A" else 999.0,
            "Raw_RSI": tech_meta["RSI_14"],
            "Is_FII": is_fii
        }
    except Exception:
        return {}

async def run_master_screener():
    print("=" * 100)
    print("🧠 ALPHA-INTELLIGENCE MULTI-FACTOR ENGINE (INSTITUTIONAL AUDIT RUN)")
    print("=" * 100)
    
    fetcher = DataIngestionEngine()
    print(f"⏳ Downloading vectorized price & disclosure matrices for {len(NSE_UNIVERSE)} assets...")
    hist_batch = fetcher.get_market_history_batch(NSE_UNIVERSE, period="2y")

    # Collect HTML fragments for the email report (DataFrame HTML tables)
    html_fragments: list[str] = []

    shortlisted_tickers = stage_1_vectorized_prefilter(hist_batch)
    print(f"⚡ Stage 1 Filter: {len(NSE_UNIVERSE)} Total Market -> {len(shortlisted_tickers)} Filtered Candidates")
    print("🔬 Stage 2 Engine: Executed Parallel FFT, Piotroski 9-Pt, and NSE NLP Extraction\n")

    results = []
    async with aiohttp.ClientSession() as session:
        tasks = [
            analyze_stock_pipeline(t, hist_batch[t], fetcher, session)
            for t in shortlisted_tickers
        ]
        completed = await asyncio.gather(*tasks)

    for item in completed:
        if item:
            results.append(item)

    if not results:
        print("No stocks currently meet minimum screening thresholds.")
        return

    df = pd.DataFrame(results)

    # 1. Foreign / Institutional Flow
    fii_df = df[df["Is_FII"] == True].sort_values(by="Raw_Score", ascending=False).head(5)
    print("=" * 100)
    print("1. 🏛️ TOP 5 INSTITUTIONAL & FOREIGN INVESTOR (FII/DII) ACCUMULATION")
    print("-" * 100)
    if not fii_df.empty:
        cols = ["Stock", "Current_Price", "Target_Sell", "Hold_Days", "Win_Prob", "Piotroski", "Catalysts"]
        print(fii_df[cols].to_string(index=False))
        try:
            html_fragments.append("<h2>1. 🏛️ TOP 5 INSTITUTIONAL & FOREIGN INVESTOR (FII/DII) ACCUMULATION</h2>")
            html_fragments.append(fii_df[cols].to_html(index=False, classes='report-table', border=0, escape=True))
        except Exception:
            pass
    else:
        print("No immediate FII block alerts in current cycle.")

    # 2. Periodic & Cyclical Bottoms (Lowest RSI + High Cycle Confidence)
    cycle_df = df.sort_values(by="Raw_RSI", ascending=True).head(5)
    print("\n" + "=" * 100)
    print("2. 🔄 TOP 5 PERIODIC & CYCLICAL REBOUND SETUPS (FFT CYCLE BOTTOMS)")
    print("-" * 100)
    cols_cycle = ["Stock", "Current_Price", "Target_Sell", "Cycle_Length", "Cycle_Conf", "RSI_14", "Hold_Days"]
    if not cycle_df.empty:
        print(cycle_df[cols_cycle].to_string(index=False))
        try:
            html_fragments.append("<h2>2. 🔄 TOP 5 PERIODIC & CYCLICAL REBOUND SETUPS (FFT CYCLE BOTTOMS)</h2>")
            html_fragments.append(cycle_df[cols_cycle].to_html(index=False, classes='report-table', border=0, escape=True))
        except Exception:
            pass
    else:
        print("No periodic/cyclical rebound setups found.")

    # 3. Undervalued Dips (High Piotroski + Low P/E)
    value_df = df[df["Raw_F_Score"] >= 6].sort_values(by="Raw_PE", ascending=True).head(5)
    print("\n" + "=" * 100)
    print("3. 🛡️ TOP 5 UNDERVALUED STOCKS AT STRUCTURAL DIPS (HIGH MARGIN OF SAFETY)")
    print("-" * 100)
    cols_val = ["Stock", "Current_Price", "Graham_Value", "P/E", "Piotroski", "Pledged%", "Category"]
    if not value_df.empty:
        print(value_df[cols_val].to_string(index=False))
        try:
            html_fragments.append("<h2>3. 🛡️ TOP 5 UNDERVALUED STOCKS AT STRUCTURAL DIPS (HIGH MARGIN OF SAFETY)</h2>")
            html_fragments.append(value_df[cols_val].to_html(index=False, classes='report-table', border=0, escape=True))
        except Exception:
            pass
    else:
        print("No undervalued dips matching thresholds.")

    # 4. Top Actionable Composite Ranking
    top10_df = df.sort_values(by="Raw_Score", ascending=False).head(10)
    print("\n" + "=" * 100)
    print("4. 🚀 TOP COMPOSITE ACTIONABLE PICKS (OVERALL CONVICTION RANKING)")
    print("-" * 100)
    cols_top = ["Stock", "Current_Price", "Target_Sell", "Hold_Days", "Win_Prob", "Category"]
    if not top10_df.empty:
        print(top10_df[cols_top].to_string(index=False))
        try:
            html_fragments.append("<h2>4. 🚀 TOP COMPOSITE ACTIONABLE PICKS (OVERALL CONVICTION RANKING)</h2>")
            html_fragments.append(top10_df[cols_top].to_html(index=False, classes='report-table', border=0, escape=True))
        except Exception:
            pass
    else:
        print("No actionable picks found.")
    print("=" * 100)

if __name__ == "__main__":
    # Capture all printed output (stdout + stderr) and email it after the run.
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
        asyncio.run(run_master_screener())

    output = buffer.getvalue()

    # Recipient can be overridden via REPORT_RECIPIENT env var.
    recipient = os.getenv("REPORT_RECIPIENT", "dkushal1109@gmail.com")
    subject = os.getenv("REPORT_SUBJECT", "Alpha Intelligence Run Output")

    try:
        if output.strip():
            # Prefer structured HTML fragments when available (DataFrame.to_html)
            if html_fragments:
                body_html = "".join(html_fragments)
                html = wrap_html(subject, body_html)
            else:
                html = format_html_report(subject, output)

            send_email(recipient, subject, output, html=html)
            print(f"Run output captured and emailed to {recipient}")
        else:
            print("No output captured; nothing to email.")
    except Exception as exc:
        print(f"Failed to send email: {exc}")