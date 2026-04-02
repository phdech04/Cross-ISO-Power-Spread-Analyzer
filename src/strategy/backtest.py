"""
Backtest engine for spread trading strategies.
Event-driven loop with P&L tracking, transaction costs, and performance metrics.
"""

import numpy as np
import pandas as pd


class BacktestEngine:
    def run(
        self,
        signals: pd.DataFrame,
        initial_capital: float = 100_000,
        position_size_mw: float = 50,
        transaction_cost: float = 0.05,
    ) -> dict:
        """
        Full backtest with:
        - P&L tracking (realized + unrealized)
        - Transaction costs ($0.05/MWh round trip)
        - Performance metrics (Sharpe, max DD, win rate, etc.)
        - Monthly P&L breakdown

        signals: DataFrame with 'spread' and 'position' columns
        """
        spreads = signals["spread"].values
        positions = signals["position"].values
        n = len(spreads)

        # Track P&L
        equity = np.zeros(n)
        equity[0] = initial_capital
        daily_pnl = np.zeros(n)
        trade_pnl = []  # individual trade results
        costs = np.zeros(n)

        # Trade tracking
        entry_price = 0.0
        current_pos = 0
        n_trades = 0

        for i in range(1, n):
            pos = positions[i]
            prev_pos = positions[i - 1]
            spread_change = spreads[i] - spreads[i - 1]

            # P&L from holding position
            holding_pnl = prev_pos * spread_change * position_size_mw
            daily_pnl[i] = holding_pnl

            # Transaction costs on position changes
            if pos != prev_pos:
                trade_size = abs(pos - prev_pos) * position_size_mw
                cost = trade_size * transaction_cost
                costs[i] = cost
                daily_pnl[i] -= cost

                # Track individual trades
                if prev_pos != 0 and (pos == 0 or np.sign(pos) != np.sign(prev_pos)):
                    trade_return = (spreads[i] - entry_price) * prev_pos * position_size_mw
                    trade_pnl.append(trade_return - cost)
                    n_trades += 1

                if pos != 0:
                    entry_price = spreads[i]

            equity[i] = equity[i - 1] + daily_pnl[i]

        # Compute metrics
        returns = pd.Series(daily_pnl[1:]) / initial_capital
        equity_series = pd.Series(equity)

        metrics = self._compute_metrics(
            returns, equity_series, trade_pnl, n_trades,
            initial_capital, costs.sum()
        )

        # Monthly breakdown
        if "spread" in signals.columns and hasattr(signals.index, "month"):
            monthly = self._monthly_breakdown(signals.index, daily_pnl)
        else:
            monthly = None

        return {
            "equity_curve": equity_series,
            "daily_pnl": pd.Series(daily_pnl),
            "metrics": metrics,
            "trade_pnl": trade_pnl,
            "total_costs": costs.sum(),
            "monthly": monthly,
        }

    def _compute_metrics(
        self, returns, equity, trade_pnl, n_trades,
        initial_capital, total_costs
    ) -> dict:
        """Compute comprehensive performance metrics."""
        total_return = (equity.iloc[-1] - initial_capital) / initial_capital

        # Sharpe ratio (annualized, assuming daily returns)
        if returns.std() > 0:
            sharpe = returns.mean() / returns.std() * np.sqrt(252)
        else:
            sharpe = 0.0

        # Sortino ratio (downside deviation only)
        downside = returns[returns < 0]
        if len(downside) > 0 and downside.std() > 0:
            sortino = returns.mean() / downside.std() * np.sqrt(252)
        else:
            sortino = 0.0

        # Max drawdown
        peak = equity.cummax()
        drawdown = (equity - peak) / peak
        max_dd = drawdown.min()

        # Calmar ratio
        if max_dd != 0:
            annual_return = total_return * (252 / len(returns)) if len(returns) > 0 else 0
            calmar = annual_return / abs(max_dd)
        else:
            calmar = 0.0

        # Win rate
        if trade_pnl:
            wins = [t for t in trade_pnl if t > 0]
            losses = [t for t in trade_pnl if t <= 0]
            win_rate = len(wins) / len(trade_pnl)
            avg_win = np.mean(wins) if wins else 0
            avg_loss = np.mean(losses) if losses else 0
            profit_factor = abs(sum(wins) / sum(losses)) if losses and sum(losses) != 0 else np.inf
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            profit_factor = 0

        return {
            "total_return": float(total_return),
            "total_return_pct": float(total_return * 100),
            "final_equity": float(equity.iloc[-1]),
            "sharpe_ratio": float(sharpe),
            "sortino_ratio": float(sortino),
            "max_drawdown": float(max_dd),
            "max_drawdown_pct": float(max_dd * 100),
            "calmar_ratio": float(calmar),
            "n_trades": n_trades,
            "win_rate": float(win_rate),
            "avg_win": float(avg_win),
            "avg_loss": float(avg_loss),
            "profit_factor": float(profit_factor),
            "total_costs": float(total_costs),
        }

    def _monthly_breakdown(self, index, daily_pnl) -> pd.DataFrame:
        """Monthly P&L summary."""
        df = pd.DataFrame({"date": index, "pnl": daily_pnl})
        df["month"] = pd.to_datetime(df["date"]).dt.to_period("M")
        return df.groupby("month")["pnl"].sum().reset_index()

    def walk_forward(
        self,
        strategy_class,
        strategy_params: dict,
        spreads: pd.Series,
        train_window: int = 60,
        test_window: int = 30,
        initial_capital: float = 100_000,
        position_size_mw: float = 50,
    ) -> dict:
        """
        Walk-forward optimization to avoid overfitting.
        Train params on window, test on next period, roll forward.

        Returns combined out-of-sample results.
        """
        n = len(spreads)
        all_equity = []
        all_trades = []
        fold_results = []
        current_equity = initial_capital

        start = 0
        fold = 0

        while start + train_window + test_window <= n:
            train_end = start + train_window
            test_end = min(train_end + test_window, n)

            # Train: generate signals on training window
            train_spreads = spreads.iloc[start:train_end]
            strategy = strategy_class(**strategy_params)
            _ = strategy.generate_signals(train_spreads)

            # Test: apply same strategy to test window
            test_spreads = spreads.iloc[train_end:test_end]
            test_signals = strategy.generate_signals(test_spreads)

            # Run backtest on test period
            result = self.run(
                test_signals,
                initial_capital=current_equity,
                position_size_mw=position_size_mw,
            )

            current_equity = result["equity_curve"].iloc[-1]
            all_equity.extend(result["equity_curve"].tolist())
            all_trades.extend(result["trade_pnl"])

            fold_results.append({
                "fold": fold,
                "train_start": start,
                "train_end": train_end,
                "test_start": train_end,
                "test_end": test_end,
                "return": result["metrics"]["total_return"],
                "sharpe": result["metrics"]["sharpe_ratio"],
                "n_trades": result["metrics"]["n_trades"],
            })

            start += test_window
            fold += 1

        # Overall out-of-sample metrics
        equity_series = pd.Series(all_equity)
        returns = equity_series.pct_change().dropna()
        overall_metrics = self._compute_metrics(
            returns, equity_series, all_trades, len(all_trades),
            initial_capital, 0
        )

        return {
            "fold_results": pd.DataFrame(fold_results),
            "overall_metrics": overall_metrics,
            "equity_curve": equity_series,
            "n_folds": fold,
        }
