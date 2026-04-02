"""
Position sizing: Kelly criterion and fixed-fractional methods.
Determines optimal trade size based on edge and risk tolerance.
"""

import numpy as np


class PositionSizer:
    def kelly_criterion(
        self, win_rate: float, avg_win: float, avg_loss: float
    ) -> float:
        """
        Kelly criterion: optimal fraction of capital to risk per trade.
        f* = (p * b - q) / b
        where p = win_rate, q = 1 - p, b = avg_win / |avg_loss|

        Returns fraction of capital (0 to 1). Often use half-Kelly in practice.
        """
        if avg_loss == 0 or win_rate <= 0 or win_rate >= 1:
            return 0.0

        b = abs(avg_win / avg_loss)
        q = 1 - win_rate
        kelly = (win_rate * b - q) / b

        return max(0.0, min(kelly, 1.0))

    def half_kelly(
        self, win_rate: float, avg_win: float, avg_loss: float
    ) -> float:
        """Half-Kelly: more conservative, reduces variance of outcomes."""
        return self.kelly_criterion(win_rate, avg_win, avg_loss) / 2

    def fixed_fractional(
        self,
        capital: float,
        risk_pct: float,
        stop_distance: float,
        price_per_mw: float = 1.0,
    ) -> float:
        """
        Position size based on fixed % risk per trade.
        position_mw = (capital * risk_pct) / (stop_distance * price_per_mw)
        """
        if stop_distance <= 0:
            return 0.0

        risk_amount = capital * risk_pct
        position = risk_amount / (stop_distance * price_per_mw)
        return float(position)

    def optimal_size(
        self,
        capital: float,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        max_risk_pct: float = 0.02,
        stop_distance: float = None,
    ) -> dict:
        """
        Recommend position size using multiple methods.
        Returns all methods for comparison.
        """
        kelly = self.kelly_criterion(win_rate, avg_win, avg_loss)
        half_k = self.half_kelly(win_rate, avg_win, avg_loss)

        result = {
            "kelly_fraction": kelly,
            "half_kelly_fraction": half_k,
            "kelly_capital": capital * kelly,
            "half_kelly_capital": capital * half_k,
        }

        if stop_distance and stop_distance > 0:
            fixed = self.fixed_fractional(capital, max_risk_pct, stop_distance)
            result["fixed_fractional_mw"] = fixed
            result["fixed_risk_amount"] = capital * max_risk_pct

        return result
