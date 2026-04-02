"""
Value-at-Risk (VaR) and Conditional VaR (CVaR / Expected Shortfall).
Historical simulation and parametric approaches.
"""

import numpy as np
import pandas as pd
from scipy.stats import norm


class RiskMetrics:
    def historical_var(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """
        Historical simulation VaR.
        Returns the loss threshold at the given confidence level.
        """
        sorted_r = np.sort(returns.dropna().values)
        index = int((1 - confidence) * len(sorted_r))
        return float(sorted_r[index])

    def parametric_var(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """Gaussian VaR — assumes normal distribution of returns."""
        mu = returns.mean()
        sigma = returns.std()
        return float(norm.ppf(1 - confidence, mu, sigma))

    def cvar(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """
        Conditional VaR (Expected Shortfall).
        Average loss in the worst (1-confidence)% of cases.
        More informative than VaR for fat-tailed distributions.
        """
        var = self.historical_var(returns, confidence)
        tail = returns[returns <= var]
        if len(tail) == 0:
            return var
        return float(tail.mean())

    def max_drawdown(self, equity_curve: pd.Series) -> dict:
        """
        Maximum drawdown: peak-to-trough decline.
        Returns drawdown value, percentage, and duration.
        """
        peak = equity_curve.cummax()
        dd = (equity_curve - peak) / peak
        max_dd = dd.min()

        # Find drawdown duration
        in_drawdown = dd < 0
        drawdown_periods = []
        start = None

        for i in range(len(in_drawdown)):
            if in_drawdown.iloc[i] and start is None:
                start = i
            elif not in_drawdown.iloc[i] and start is not None:
                drawdown_periods.append(i - start)
                start = None

        if start is not None:
            drawdown_periods.append(len(in_drawdown) - start)

        max_duration = max(drawdown_periods) if drawdown_periods else 0

        return {
            "max_drawdown": float(max_dd),
            "max_drawdown_pct": float(max_dd * 100),
            "max_duration_periods": max_duration,
            "current_drawdown": float(dd.iloc[-1]),
        }

    def rolling_var(
        self, returns: pd.Series, window: int = 60, confidence: float = 0.95
    ) -> pd.Series:
        """Rolling historical VaR over a window."""
        return returns.rolling(window).apply(
            lambda x: np.percentile(x, (1 - confidence) * 100)
        )

    def risk_report(
        self, returns: pd.Series, equity_curve: pd.Series, confidence: float = 0.95
    ) -> dict:
        """Comprehensive risk report."""
        return {
            "historical_var_95": self.historical_var(returns, 0.95),
            "historical_var_99": self.historical_var(returns, 0.99),
            "parametric_var_95": self.parametric_var(returns, 0.95),
            "cvar_95": self.cvar(returns, 0.95),
            "cvar_99": self.cvar(returns, 0.99),
            "drawdown": self.max_drawdown(equity_curve),
            "volatility_annual": float(returns.std() * np.sqrt(252)),
            "skewness": float(returns.skew()),
            "kurtosis": float(returns.kurtosis()),
            "worst_day": float(returns.min()),
            "best_day": float(returns.max()),
        }
