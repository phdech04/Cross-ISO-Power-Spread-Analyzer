import pytest
import numpy as np
import pandas as pd
from src.risk.var import RiskMetrics


class TestRiskMetrics:
    @pytest.fixture
    def risk(self):
        return RiskMetrics()

    @pytest.fixture
    def normal_returns(self):
        np.random.seed(42)
        return pd.Series(np.random.randn(1000) * 0.02)

    def test_historical_var_negative(self, risk, normal_returns):
        """VaR at 95% should be negative (a loss)."""
        var = risk.historical_var(normal_returns, 0.95)
        assert var < 0

    def test_var_99_worse_than_95(self, risk, normal_returns):
        """99% VaR should be more extreme than 95% VaR."""
        var_95 = risk.historical_var(normal_returns, 0.95)
        var_99 = risk.historical_var(normal_returns, 0.99)
        assert var_99 < var_95

    def test_cvar_worse_than_var(self, risk, normal_returns):
        """CVaR should be more extreme than VaR (it's the tail average)."""
        var = risk.historical_var(normal_returns, 0.95)
        cvar = risk.cvar(normal_returns, 0.95)
        assert cvar <= var

    def test_parametric_var_close_to_historical(self, risk, normal_returns):
        """For normal data, parametric and historical VaR should be similar."""
        hist = risk.historical_var(normal_returns, 0.95)
        param = risk.parametric_var(normal_returns, 0.95)
        assert abs(hist - param) < 0.02

    def test_max_drawdown_bounded(self, risk):
        """Max drawdown should be between -1 and 0."""
        equity = pd.Series([100, 110, 105, 95, 100, 108, 90, 95])
        dd = risk.max_drawdown(equity)
        assert -1 <= dd["max_drawdown"] <= 0

    def test_risk_report_complete(self, risk, normal_returns):
        """Risk report should contain all expected keys."""
        equity = (1 + normal_returns).cumprod() * 100000
        report = risk.risk_report(normal_returns, equity)
        expected_keys = [
            "historical_var_95", "historical_var_99",
            "parametric_var_95", "cvar_95", "cvar_99",
            "drawdown", "volatility_annual",
        ]
        for key in expected_keys:
            assert key in report
