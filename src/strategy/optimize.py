"""
Strategy parameter optimization with walk-forward validation.
Grid search over parameter combinations, ranked by Sharpe ratio.
"""

import logging
from itertools import product

import numpy as np
import pandas as pd

from src.strategy.backtest import BacktestEngine

logger = logging.getLogger(__name__)


class StrategyOptimizer:
    def __init__(self):
        self.engine = BacktestEngine()

    def grid_search(
        self,
        strategy_class,
        spreads: pd.Series,
        param_grid: dict,
        train_window: int = 60,
        test_window: int = 30,
        top_n: int = 10,
    ) -> pd.DataFrame:
        """
        Test parameter combinations with walk-forward validation.
        Returns top N parameter sets by Sharpe ratio.

        param_grid: dict of param_name -> list of values
            e.g. {"lookback": [10, 20, 30], "entry_z": [1.0, 1.5, 2.0]}
        """
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(product(*param_values))

        results = []
        total = len(combinations)

        for i, combo in enumerate(combinations):
            params = dict(zip(param_names, combo))
            logger.info(f"Testing {i+1}/{total}: {params}")

            try:
                wf = self.engine.walk_forward(
                    strategy_class=strategy_class,
                    strategy_params=params,
                    spreads=spreads,
                    train_window=train_window,
                    test_window=test_window,
                )

                row = {**params}
                row.update({
                    "sharpe": wf["overall_metrics"]["sharpe_ratio"],
                    "total_return": wf["overall_metrics"]["total_return"],
                    "max_drawdown": wf["overall_metrics"]["max_drawdown"],
                    "win_rate": wf["overall_metrics"]["win_rate"],
                    "n_trades": wf["overall_metrics"]["n_trades"],
                    "n_folds": wf["n_folds"],
                })
                results.append(row)

            except Exception as e:
                logger.warning(f"Failed for {params}: {e}")

        if not results:
            return pd.DataFrame()

        df = pd.DataFrame(results)
        df = df.sort_values("sharpe", ascending=False).head(top_n)
        return df.reset_index(drop=True)

    def sensitivity_analysis(
        self,
        strategy_class,
        spreads: pd.Series,
        base_params: dict,
        param_name: str,
        param_range: list,
    ) -> pd.DataFrame:
        """
        How sensitive is performance to a single parameter?
        Varies one param while holding others constant.
        """
        results = []

        for value in param_range:
            params = {**base_params, param_name: value}
            try:
                strategy = strategy_class(**params)
                signals = strategy.generate_signals(spreads)
                result = self.engine.run(signals)

                results.append({
                    param_name: value,
                    "sharpe": result["metrics"]["sharpe_ratio"],
                    "total_return": result["metrics"]["total_return"],
                    "max_drawdown": result["metrics"]["max_drawdown"],
                    "n_trades": result["metrics"]["n_trades"],
                })
            except Exception as e:
                logger.warning(f"Failed for {param_name}={value}: {e}")

        return pd.DataFrame(results)
