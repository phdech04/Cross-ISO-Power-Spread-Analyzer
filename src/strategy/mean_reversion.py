"""
Z-score mean reversion strategy for power spreads.
Trades spread convergence when it deviates significantly from its mean.
"""

import numpy as np
import pandas as pd


class MeanReversionStrategy:
    def __init__(
        self,
        lookback: int = 20,
        entry_z: float = 1.5,
        exit_z: float = 0.3,
        stop_loss_z: float = 3.0,
    ):
        self.lookback = lookback
        self.entry_z = entry_z
        self.exit_z = exit_z
        self.stop_loss_z = stop_loss_z

    def generate_signals(self, spreads: pd.Series) -> pd.DataFrame:
        """
        Signal logic:
        - LONG spread when z < -entry_z (spread unusually tight → expect widening)
        - SHORT spread when z > +entry_z (spread unusually wide → expect tightening)
        - EXIT when z crosses back through exit_z toward zero
        - STOP when |z| exceeds stop_loss_z (regime break, cut losses)

        Returns DataFrame with columns: [spread, zscore, signal, position]
        signal: 1 = long, -1 = short, 0 = flat
        """
        rolling_mean = spreads.rolling(self.lookback).mean()
        rolling_std = spreads.rolling(self.lookback).std()
        zscore = (spreads - rolling_mean) / rolling_std

        signals = pd.DataFrame({
            "spread": spreads,
            "zscore": zscore,
            "signal": 0,
            "position": 0,
        })

        position = 0
        for i in range(self.lookback, len(signals)):
            z = zscore.iloc[i]

            if np.isnan(z):
                signals.iloc[i, signals.columns.get_loc("position")] = position
                continue

            # Stop loss
            if abs(z) > self.stop_loss_z and position != 0:
                signals.iloc[i, signals.columns.get_loc("signal")] = -position  # close
                position = 0

            # Entry signals
            elif z < -self.entry_z and position <= 0:
                signals.iloc[i, signals.columns.get_loc("signal")] = 1
                position = 1

            elif z > self.entry_z and position >= 0:
                signals.iloc[i, signals.columns.get_loc("signal")] = -1
                position = -1

            # Exit signals
            elif position == 1 and z > -self.exit_z:
                signals.iloc[i, signals.columns.get_loc("signal")] = -1  # close long
                position = 0

            elif position == -1 and z < self.exit_z:
                signals.iloc[i, signals.columns.get_loc("signal")] = 1  # close short
                position = 0

            signals.iloc[i, signals.columns.get_loc("position")] = position

        return signals

    def get_params(self) -> dict:
        return {
            "lookback": self.lookback,
            "entry_z": self.entry_z,
            "exit_z": self.exit_z,
            "stop_loss_z": self.stop_loss_z,
        }
