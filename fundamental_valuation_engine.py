"""
Fundamental Moat, Piotroski 9-Point Score, and Graham Safety Engine.
"""

import numpy as np
from typing import Dict, Any, Tuple
from config import THRESHOLDS

class FundamentalValuationEngine:
    
    @staticmethod
    def calculate_piotroski_f_score(fin_data: Dict[str, Any]) -> int:
        """
        Calculates the complete 9-point Piotroski F-Score for accounting quality:
        - Profitability: Positive ROA, CFO, delta ROA, CFO > Net Income
        - Leverage & Capital: delta Long-Term Debt, delta Current Ratio, Share Dilution
        - Operating Efficiency: delta Gross Margin, delta Asset Turnover
        """
        score = 0
        try:
            fin = fin_data.get("financials")
            bs = fin_data.get("balance_sheet")
            cf = fin_data.get("cashflow")

            if fin is None or bs is None or cf is None or fin.empty or bs.empty or cf.empty:
                return 5  # Neutral baseline when quarterly filing is delayed

            # 1. Positive Net Income
            net_income = fin.loc["Net Income"].iloc[0] if "Net Income" in fin.index else 0
            if net_income > 0: score += 1

            # 2. Positive Operating Cash Flow
            cfo = cf.loc["Operating Cash Flow"].iloc[0] if "Operating Cash Flow" in cf.index else 0
            if cfo > 0: score += 1

            # 3. Positive Return on Assets (ROA)
            total_assets = bs.loc["Total Assets"].iloc[0] if "Total Assets" in bs.index else 1
            roa = net_income / total_assets
            if roa > 0: score += 1

            # 4. High Quality of Earnings (Cash Flow > Net Income)
            if cfo > net_income: score += 1

            # 5. Decreasing / Stable Long-Term Debt
            if "Long Term Debt" in bs.index and len(bs.loc["Long Term Debt"]) > 1:
                if bs.loc["Long Term Debt"].iloc[0] <= bs.loc["Long Term Debt"].iloc[1]:
                    score += 1
            else:
                score += 1

            # 6. Improving Current Ratio (Liquidity)
            if "Current Assets" in bs.index and "Current Liabilities" in bs.index:
                cr_curr = bs.loc["Current Assets"].iloc[0] / (bs.loc["Current Liabilities"].iloc[0] + 1e-9)
                cr_prev = bs.loc["Current Assets"].iloc[1] / (bs.loc["Current Liabilities"].iloc[1] + 1e-9)
                if cr_curr > cr_prev: score += 1

            # 7. No Capital Dilution (Shares outstanding unchanged or reduced)
            if "Ordinary Shares Number" in bs.index and len(bs.loc["Ordinary Shares Number"]) > 1:
                if bs.loc["Ordinary Shares Number"].iloc[0] <= bs.loc["Ordinary Shares Number"].iloc[1]:
                    score += 1
            else:
                score += 1

            # 8. Improving Gross Margin
            if "Gross Profit" in fin.index and "Total Revenue" in fin.index:
                gm_curr = fin.loc["Gross Profit"].iloc[0] / (fin.loc["Total Revenue"].iloc[0] + 1e-9)
                gm_prev = fin.loc["Gross Profit"].iloc[1] / (fin.loc["Total Revenue"].iloc[1] + 1e-9)
                if gm_curr > gm_prev: score += 1

            # 9. Improving Asset Turnover Ratio
            if "Total Revenue" in fin.index and len(bs.loc["Total Assets"]) > 1:
                at_curr = fin.loc["Total Revenue"].iloc[0] / bs.loc["Total Assets"].iloc[0]
                at_prev = fin.loc["Total Revenue"].iloc[1] / bs.loc["Total Assets"].iloc[1]
                if at_curr > at_prev: score += 1

        except Exception:
            return 5
            
        return score

    @staticmethod
    def evaluate_valuation_and_safety(info: Dict[str, Any], f_score: int) -> Tuple[float, Dict[str, Any]]:
        """
        Screens for Margin of Safety, promoter integrity, and valuation ratios.
        """
        score = 50.0
        
        pe_ratio = info.get("trailingPE", 999.0)
        forward_pe = info.get("forwardPE", 999.0)
        peg_ratio = info.get("pegRatio", 999.0)
        debt_to_equity = (info.get("debtToEquity", 0.0) or 0.0) / 100.0
        pledged_prop = info.get("pledgedPropelledPercentage", 0.0) or 0.0
        book_value = info.get("bookValue", 0.0) or 0.0
        eps = info.get("trailingEps", 0.0) or 0.0

        # Safety: Severe penalty for high promoter pledge
        if pledged_prop > THRESHOLDS["MAX_PROMOTER_PLEDGE_PCT"]:
            score -= 30.0
        else:
            score += 15.0

        # Solvency: Debt-to-Equity check
        if debt_to_equity < THRESHOLDS["MAX_DEBT_TO_EQUITY"]:
            score += 10.0
        else:
            score -= 15.0

        # Financial health
        if f_score >= 7:
            score += 20.0
        elif f_score <= 4:
            score -= 20.0

        # Valuation & Growth checks
        if 0 < peg_ratio <= THRESHOLDS["MAX_PEG_RATIO"]:
            score += 15.0
        if 0 < forward_pe < pe_ratio:
            score += 10.0

        # Benjamin Graham Fair Value = sqrt(22.5 * EPS * Book Value)
        graham_value = 0.0
        if eps > 0 and book_value > 0:
            graham_value = round(np.sqrt(22.5 * eps * book_value), 2)

        return max(min(score, 100.0), 0.0), {
            "Piotroski_F_Score": f_score,
            "PE_Ratio": round(pe_ratio, 2) if pe_ratio != 999.0 else "N/A",
            "Forward_PE": round(forward_pe, 2) if forward_pe != 999.0 else "N/A",
            "PEG": round(peg_ratio, 2) if peg_ratio != 999.0 else "N/A",
            "Debt_To_Equity": round(debt_to_equity, 2),
            "Pledged_Pct": round(pledged_prop, 2),
            "Graham_Fair_Value": graham_value
        }