"""
Trend-following / momentum strategy on spreads.
Uses moving average crossover to capture regime shifts
that mean-reversion misses.
"""

import numpy as np
import pandas as pd


class MomentumStrategy:
    def __init__(self, fast_window: int = 5, slow_window: int = 20):
        self.fast_window = fast_window
        self.slow_window = slow_window

    def generate_signals(self, spreads: pd.Series) -> pd.DataFrame:
        """
        Moving average crossover on spread.
        - LONG when fast MA > slow MA (spread trending up)
        - SHORT when fast MA < slow MA (spread trending down)

        Returns DataFrame with columns: [spread, fast_ma, slow_ma, signal, position]
        """
        fast_ma = spreads.rolling(self.fast_window).mean()
        slow_ma = spreads.rolling(self.slow_window).mean()

        signals = pd.DataFrame({
            "spread": spreads,
            "fast_ma": fast_ma,
            "slow_ma": slow_ma,
            "signal": 0,
            "position": 0,
        })

        position = 0
        prev_fast = np.nan
        prev_slow = np.nan

        for i in range(self.slow_window, len(signals)):
            f = fast_ma.iloc[i]
            s = slow_ma.iloc[i]

            if np.isnan(f) or np.isnan(s):
                signals.iloc[i, signals.columns.get_loc("position")] = position
                prev_fast, prev_slow = f, s
                continue

            # Crossover detection
            if not np.isnan(prev_fast) and not np.isnan(prev_slow):
                # Bullish crossover
                if prev_fast <= prev_slow and f > s and position != 1:
                    signals.iloc[i, signals.columns.get_loc("signal")] = 1
                    position = 1

                # Bearish crossover
                elif prev_fast >= prev_slow and f < s and position != -1:
                    signals.iloc[i, signals.columns.get_loc("signal")] = -1
                    position = -1

            signals.iloc[i, signals.columns.get_loc("position")] = position
            prev_fast, prev_slow = f, s

        return signals

    def get_params(self) -> dict:
        return {
            "fast_window": self.fast_window,
            "slow_window": self.slow_window,
        }
