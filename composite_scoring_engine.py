"""
Multi-Factor Synthesis, Conviction Probability, and Action Categorization.
"""

from typing import List
from config import WEIGHTS

class CompositeScoringEngine:

    @staticmethod
    def synthesize_score(
        fund_score: float, 
        tech_score: float, 
        catalyst_score: float, 
        inst_score: float,
        has_volume_breakout: bool = False
    ) -> float:
        """
        Ensemble weighting across valuation, technical cycle, news catalysts, and smart money flows.
        """
        composite = (
            (fund_score * WEIGHTS["FUNDAMENTAL_VALUE"]) +
            (tech_score * WEIGHTS["TECHNICAL_CYCLE"]) +
            (catalyst_score * WEIGHTS["CATALYST_ORDERBOOK"]) +
            (inst_score * WEIGHTS["INSTITUTIONAL_FLOW"])
        )
        
        # Add volume breakout booster
        if has_volume_breakout:
            composite += 8.0
            
        return round(min(composite, 98.0), 2)

    @staticmethod
    def categorize_opportunity(score: float, catalysts: List[str], f_score: int, has_volume_breakout: bool) -> str:
        """
        Categorizes actionable setups for early-profit swing trading or high-growth multibaggers.
        """
        if has_volume_breakout and "Massive Order Win" in catalysts:
            return "🚀 Small-Cap Multibagger Breakout"
        elif "Massive Order Win" in catalysts and score >= 70.0:
            return "📦 Order Book Expansion Play"
        elif "FII/DII Accumulation" in catalysts and f_score >= 7:
            return "💎 Institutional Accumulation Bottom"
        elif score >= 70.0 and f_score >= 6:
            return "📈 Undervalued Mean-Reversion Swing"
        elif score >= 60.0:
            return "⏳ Early Watchlist Catalyst"
        else:
            return "⚠️ Neutral / Extended"