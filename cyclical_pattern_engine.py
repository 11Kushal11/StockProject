"""
Fast Fourier Transform (FFT) Periodicity, Mean-Reversion, and Swing Recovery Duration.
"""

import numpy as np
import pandas as pd
from scipy.fft import rfft, rfftfreq
from datetime import timedelta
from typing import Tuple, Dict, Any

class CyclicalPatternEngine:

    @staticmethod
    def detect_dominant_cycle_length(prices: pd.Series) -> Tuple[int, float]:
        """
        Performs Fast Fourier Transform (FFT) on log returns to identify
        the dominant cyclical swing rhythm (in trading days).
        """
        try:
            log_returns = np.diff(np.log(prices.values))
            n = len(log_returns)
            if n < 60:
                return 21, 0.5

            fourier = rfft(log_returns)
            power = np.abs(fourier) ** 2
            freq = rfftfreq(n, d=1)

            power[0] = 0  # Remove 0-frequency DC component
            dominant_idx = np.argmax(power)
            dominant_freq = freq[dominant_idx]

            if dominant_freq > 0:
                cycle_length = int(round(1.0 / dominant_freq))
                total_power = np.sum(power)
                confidence = float(power[dominant_idx] / (total_power + 1e-9))
                
                if 10 <= cycle_length <= 90:
                    return cycle_length, min(confidence * 5.0, 1.0)
        except Exception:
            pass
        return 21, 0.5

    @staticmethod
    def calculate_technical_confluence(df: pd.DataFrame) -> Tuple[float, int, float, Dict[str, Any]]:
        """
        Evaluates structural 200 EMA support, 14 RSI oversold rebounds,
        FFT cycle bottoms, and historical mean-reversion recovery days.
        """
        close = df["Close"]
        curr_price = float(close.iloc[-1])
        
        # Exponential Moving Averages
        ema_50 = float(close.ewm(span=50, adjust=False).mean().iloc[-1])
        ema_200 = float(close.ewm(span=200, adjust=False).mean().iloc[-1])
        
        # 14-day Relative Strength Index (RSI)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        rsi_series = 100 - (100 / (1 + rs))
        curr_rsi = float(rsi_series.iloc[-1])

        # Cyclical FFT periodicity
        cycle_days, cycle_conf = CyclicalPatternEngine.detect_dominant_cycle_length(close)

        # Historical recovery speed to achieve +5% profit from similar oversold dips
        dip_dates = rsi_series[rsi_series <= 45].index
        recovery_durations = []
        target_pct = 0.05
        
        for dip in dip_dates:
            future = close.loc[dip : dip + timedelta(days=40)]
            if len(future) > 1:
                entry = future.iloc[0]
                target = entry * (1.0 + target_pct)
                hit = future[future >= target]
                if not hit.empty:
                    days_taken = (hit.index[0] - dip).days
                    recovery_durations.append(days_taken)

        est_recovery_days = int(np.median(recovery_durations)) if recovery_durations else cycle_days

        # Technical Confluence Scoring
        score = 40.0
        if curr_rsi <= 35.0:
            score += 25.0
        elif curr_rsi <= 45.0:
            score += 15.0

        if curr_price >= (ema_200 * 0.95):  # Above structural macro trendline
            score += 15.0
        if curr_price > ema_50:
            score += 10.0
            
        score += (cycle_conf * 10.0)

        tech_score = max(min(score, 100.0), 0.0)
        target_price = round(curr_price * (1.0 + target_pct), 2)

        return tech_score, est_recovery_days, target_price, {
            "RSI_14": round(curr_rsi, 1),
            "Dominant_Cycle_Days": cycle_days,
            "Cycle_Confidence": round(cycle_conf, 2),
            "Above_200_EMA": curr_price >= ema_200
        }