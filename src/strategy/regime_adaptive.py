"""
Regime-adaptive mean reversion strategy.
Dynamically adjusts entry/exit thresholds and position sizing
based on HMM-detected volatility regime.
"""

import numpy as np
import pandas as pd

from src.analysis.regime import RegimeDetector


# Default parameter sets per regime
REGIME_PARAMS = {
    0: {  # low_volatility
        "entry_z": 2.0,
        "exit_z": 0.5,
        "stop_loss_z": 3.5,
        "position_scale": 1.0,
        "label": "low_volatility",
    },
    1: {  # normal
        "entry_z": 1.5,
        "exit_z": 0.3,
        "stop_loss_z": 3.0,
        "position_scale": 1.0,
        "label": "normal",
    },
    2: {  # high_volatility
        "entry_z": 1.0,
        "exit_z": 0.2,
        "stop_loss_z": 2.0,
        "position_scale": 0.5,
        "label": "high_volatility",
    },
}


class RegimeAdaptiveStrategy:
    """
    Mean-reversion strategy that adapts parameters to the current
    volatility regime detected by the HMM.
    """

    def __init__(
        self,
        lookback: int = 20,
        regime_params: dict = None,
        regime_lookback: int = 60,
    ):
        self.lookback = lookback
        self.regime_params = regime_params or REGIME_PARAMS
        self.regime_lookback = regime_lookback
        self.detector = RegimeDetector()

    def generate_signals(self, spreads: pd.Series) -> pd.DataFrame:
        """
        Regime-adaptive signal generation.
        1. Detect current regime from recent return volatility
        2. Select entry/exit parameters for that regime
        3. Generate z-score signals with adapted thresholds
        """
        # Compute returns for regime detection
        returns = spreads.pct_change().dropna()
        if len(returns) < self.regime_lookback:
            # Fall back to default params
            regime_result = None
            states = np.ones(len(spreads), dtype=int)  # all "normal"
        else:
            regime_result = self.detector.fit(returns)
            states = regime_result["states"]
            # Pad to match spreads length (first values get state 1=normal)
            pad = len(spreads) - len(states)
            states = np.concatenate([np.ones(pad, dtype=int), states])

        # Rolling z-score
        rolling_mean = spreads.rolling(self.lookback).mean()
        rolling_std = spreads.rolling(self.lookback).std()
        zscore = (spreads - rolling_mean) / rolling_std

        signals = pd.DataFrame({
            "spread": spreads.values,
            "zscore": zscore.values,
            "signal": 0,
            "position": 0,
            "regime": states,
            "regime_label": [self.regime_params.get(s, self.regime_params[1])["label"] for s in states],
            "entry_z_used": 0.0,
            "position_scale": 1.0,
        })

        position = 0

        for i in range(self.lookback, len(signals)):
            z = zscore.iloc[i]
            if np.isnan(z):
                signals.iloc[i, signals.columns.get_loc("position")] = position
                continue

            # Get regime-specific parameters
            regime = int(states[i])
            params = self.regime_params.get(regime, self.regime_params[1])
            entry_z = params["entry_z"]
            exit_z = params["exit_z"]
            stop_z = params["stop_loss_z"]
            scale = params["position_scale"]

            signals.iloc[i, signals.columns.get_loc("entry_z_used")] = entry_z
            signals.iloc[i, signals.columns.get_loc("position_scale")] = scale

            # Stop loss
            if abs(z) > stop_z and position != 0:
                signals.iloc[i, signals.columns.get_loc("signal")] = -position
                position = 0

            # Entry
            elif z < -entry_z and position <= 0:
                signals.iloc[i, signals.columns.get_loc("signal")] = 1
                position = 1

            elif z > entry_z and position >= 0:
                signals.iloc[i, signals.columns.get_loc("signal")] = -1
                position = -1

            # Exit
            elif position == 1 and z > -exit_z:
                signals.iloc[i, signals.columns.get_loc("signal")] = -1
                position = 0

            elif position == -1 and z < exit_z:
                signals.iloc[i, signals.columns.get_loc("signal")] = 1
                position = 0

            signals.iloc[i, signals.columns.get_loc("position")] = position

        return signals

    def get_regime_summary(self, signals: pd.DataFrame) -> dict:
        """Summary of regime distribution and performance."""
        regimes = signals["regime_label"].value_counts()
        return {
            "regime_distribution": regimes.to_dict(),
            "regime_pct": (regimes / len(signals) * 100).round(1).to_dict(),
            "current_regime": signals["regime_label"].iloc[-1],
            "current_entry_z": float(signals["entry_z_used"].iloc[-1]),
            "current_position_scale": float(signals["position_scale"].iloc[-1]),
        }

    def get_params(self) -> dict:
        return {
            "lookback": self.lookback,
            "regime_lookback": self.regime_lookback,
            "regime_params": {
                k: {kk: vv for kk, vv in v.items()}
                for k, v in self.regime_params.items()
            },
        }
