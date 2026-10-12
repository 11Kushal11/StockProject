"""
Liquidity Verification, Circuit Freeze Prevention, and Unusual Volume Accumulation.
"""

import pandas as pd
import numpy as np
from typing import Tuple

class SmallCapGrowthEngine:

    @staticmethod
    def verify_liquidity_and_circuits(df: pd.DataFrame, min_daily_turnover_cr: float = 0.75) -> bool:
        """
        Guards capital by ensuring the asset has minimum daily turnover
        and is not frozen in low-volume upper/lower circuit traps.
        """
        try:
            recent = df.tail(10)
            avg_volume = recent["Volume"].mean()
            curr_price = float(recent["Close"].iloc[-1])
            
            # Daily turnover approximation: (Price * Volume) / 10,000,000 (1 Cr)
            daily_turnover_cr = (curr_price * avg_volume) / 1e7
            
            # Check price variation (if High == Low consistently, stock is locked in circuit)
            price_spread = (recent["High"] - recent["Low"]).mean()
            is_circuit_locked = price_spread < (curr_price * 0.0005)

            if daily_turnover_cr >= min_daily_turnover_cr and not is_circuit_locked:
                return True
        except Exception:
            pass
        return False

    @staticmethod
    def detect_volume_catalyst(df: pd.DataFrame) -> Tuple[float, bool]:
        """
        Detects smart money / institutional volume breakouts:
        Checks if current volume is substantially higher than the 20-day moving average.
        """
        try:
            vol = df["Volume"]
            avg_vol_20 = vol.rolling(window=20).mean().iloc[-1]
            curr_vol = vol.iloc[-1]

            vol_ratio = curr_vol / (avg_vol_20 + 1e-9)
            
            if vol_ratio >= 2.5:
                return 30.0, True  # High volume surge
            elif vol_ratio >= 1.5:
                return 15.0, False # Moderate volume interest
        except Exception:
            pass
        return 0.0, False