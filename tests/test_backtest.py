import pytest
import numpy as np
import pandas as pd
from src.strategy.mean_reversion import MeanReversionStrategy
from src.strategy.momentum import MomentumStrategy
from src.strategy.backtest import BacktestEngine


class TestMeanReversionStrategy:
    def test_signals_shape(self):
        spreads = pd.Series(np.random.randn(200).cumsum())
        strategy = MeanReversionStrategy()
        signals = strategy.generate_signals(spreads)
        assert len(signals) == len(spreads)
        assert "position" in signals.columns
        assert "zscore" in signals.columns

    def test_positions_bounded(self):
        spreads = pd.Series(np.random.randn(200).cumsum())
        strategy = MeanReversionStrategy()
        signals = strategy.generate_signals(spreads)
        assert signals["position"].isin([-1, 0, 1]).all()


class TestMomentumStrategy:
    def test_signals_shape(self):
        spreads = pd.Series(np.random.randn(200).cumsum())
        strategy = MomentumStrategy()
        signals = strategy.generate_signals(spreads)
        assert len(signals) == len(spreads)
        assert "position" in signals.columns

    def test_positions_bounded(self):
        spreads = pd.Series(np.random.randn(200).cumsum())
        strategy = MomentumStrategy()
        signals = strategy.generate_signals(spreads)
        assert signals["position"].isin([-1, 0, 1]).all()


class TestBacktestEngine:
    @pytest.fixture
    def engine(self):
        return BacktestEngine()

    def test_equity_starts_at_initial_capital(self, engine):
        spreads = pd.Series(np.random.randn(100).cumsum())
        strategy = MeanReversionStrategy()
        signals = strategy.generate_signals(spreads)
        result = engine.run(signals, initial_capital=100_000)
        assert result["equity_curve"].iloc[0] == 100_000

    def test_metrics_keys(self, engine):
        spreads = pd.Series(np.random.randn(200).cumsum())
        strategy = MeanReversionStrategy()
        signals = strategy.generate_signals(spreads)
        result = engine.run(signals)
        required = ["total_return", "sharpe_ratio", "max_drawdown",
                     "win_rate", "n_trades", "profit_factor"]
        for key in required:
            assert key in result["metrics"]

    def test_no_trades_on_flat_signal(self, engine):
        signals = pd.DataFrame({
            "spread": np.random.randn(100),
            "position": np.zeros(100),
        })
        result = engine.run(signals)
        assert result["metrics"]["n_trades"] == 0
