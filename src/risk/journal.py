"""
Persistent trade journal with full attribution.
Logs every trade with strategy, regime, weather, and performance context.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class Trade:
    """A single trade record."""

    def __init__(
        self,
        pair: str,
        direction: str,
        entry_price: float,
        entry_date: str,
        strategy: str,
        regime: str = "unknown",
        weather_temp: float = None,
        position_size_mw: float = 50,
    ):
        self.id = f"{pair}_{entry_date}_{datetime.utcnow().timestamp():.0f}"
        self.pair = pair
        self.direction = direction
        self.entry_price = entry_price
        self.entry_date = entry_date
        self.exit_price = None
        self.exit_date = None
        self.strategy = strategy
        self.regime_at_entry = regime
        self.regime_at_exit = None
        self.weather_temp = weather_temp
        self.position_size_mw = position_size_mw
        self.pnl = None
        self.status = "open"
        self.notes = ""

    def close(self, exit_price: float, exit_date: str, regime: str = None):
        multiplier = 1 if self.direction == "long" else -1
        self.exit_price = exit_price
        self.exit_date = exit_date
        self.regime_at_exit = regime
        self.pnl = multiplier * (exit_price - self.entry_price) * self.position_size_mw
        self.status = "closed"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pair": self.pair,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "entry_date": self.entry_date,
            "exit_price": self.exit_price,
            "exit_date": self.exit_date,
            "strategy": self.strategy,
            "regime_at_entry": self.regime_at_entry,
            "regime_at_exit": self.regime_at_exit,
            "weather_temp": self.weather_temp,
            "position_size_mw": self.position_size_mw,
            "pnl": round(self.pnl, 2) if self.pnl is not None else None,
            "status": self.status,
            "notes": self.notes,
        }


class TradeJournal:
    """Persistent trade log with analytics."""

    def __init__(self, journal_path: str = "data/trade_journal.json"):
        self.journal_path = Path(journal_path)
        self.journal_path.parent.mkdir(parents=True, exist_ok=True)
        self.trades: List[Trade] = []
        self._load()

    def _load(self):
        if self.journal_path.exists():
            try:
                with open(self.journal_path) as f:
                    data = json.load(f)
                for t in data:
                    trade = Trade(
                        pair=t["pair"], direction=t["direction"],
                        entry_price=t["entry_price"], entry_date=t["entry_date"],
                        strategy=t["strategy"], regime=t.get("regime_at_entry", "unknown"),
                        weather_temp=t.get("weather_temp"),
                        position_size_mw=t.get("position_size_mw", 50),
                    )
                    trade.id = t["id"]
                    trade.exit_price = t.get("exit_price")
                    trade.exit_date = t.get("exit_date")
                    trade.regime_at_exit = t.get("regime_at_exit")
                    trade.pnl = t.get("pnl")
                    trade.status = t.get("status", "open")
                    trade.notes = t.get("notes", "")
                    self.trades.append(trade)
            except Exception as e:
                logger.error(f"Failed to load journal: {e}")

    def _save(self):
        with open(self.journal_path, "w") as f:
            json.dump([t.to_dict() for t in self.trades], f, indent=2)

    def open_trade(self, **kwargs) -> Trade:
        trade = Trade(**kwargs)
        self.trades.append(trade)
        self._save()
        logger.info(f"Opened trade: {trade.pair} {trade.direction} @ {trade.entry_price}")
        return trade

    def close_trade(self, trade_id: str, exit_price: float,
                    exit_date: str, regime: str = None) -> Optional[Trade]:
        for trade in self.trades:
            if trade.id == trade_id and trade.status == "open":
                trade.close(exit_price, exit_date, regime)
                self._save()
                logger.info(f"Closed trade: {trade.pair} PnL={trade.pnl:.2f}")
                return trade
        return None

    def get_open_trades(self) -> List[dict]:
        return [t.to_dict() for t in self.trades if t.status == "open"]

    def get_closed_trades(self) -> List[dict]:
        return [t.to_dict() for t in self.trades if t.status == "closed"]

    def get_all_trades(self) -> List[dict]:
        return [t.to_dict() for t in self.trades]

    def summary(self) -> dict:
        """Performance summary across all closed trades."""
        closed = [t for t in self.trades if t.status == "closed" and t.pnl is not None]
        if not closed:
            return {
                "total_trades": 0, "total_pnl": 0, "win_rate": 0,
                "avg_win": 0, "avg_loss": 0, "profit_factor": 0,
                "best_trade": 0, "worst_trade": 0,
                "by_strategy": {}, "by_regime": {}, "by_pair": {},
            }

        pnls = [t.pnl for t in closed]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]

        # Attribution by strategy
        by_strategy = {}
        for t in closed:
            s = t.strategy
            if s not in by_strategy:
                by_strategy[s] = {"trades": 0, "pnl": 0, "wins": 0}
            by_strategy[s]["trades"] += 1
            by_strategy[s]["pnl"] += t.pnl
            if t.pnl > 0:
                by_strategy[s]["wins"] += 1
        for s in by_strategy:
            by_strategy[s]["pnl"] = round(by_strategy[s]["pnl"], 2)
            by_strategy[s]["win_rate"] = round(
                by_strategy[s]["wins"] / by_strategy[s]["trades"], 3
            )

        # Attribution by regime
        by_regime = {}
        for t in closed:
            r = t.regime_at_entry
            if r not in by_regime:
                by_regime[r] = {"trades": 0, "pnl": 0, "wins": 0}
            by_regime[r]["trades"] += 1
            by_regime[r]["pnl"] += t.pnl
            if t.pnl > 0:
                by_regime[r]["wins"] += 1
        for r in by_regime:
            by_regime[r]["pnl"] = round(by_regime[r]["pnl"], 2)

        # Attribution by pair
        by_pair = {}
        for t in closed:
            p = t.pair
            if p not in by_pair:
                by_pair[p] = {"trades": 0, "pnl": 0}
            by_pair[p]["trades"] += 1
            by_pair[p]["pnl"] = round(by_pair[p]["pnl"] + t.pnl, 2)

        return {
            "total_trades": len(closed),
            "total_pnl": round(sum(pnls), 2),
            "win_rate": round(len(wins) / len(closed), 3),
            "avg_win": round(sum(wins) / len(wins), 2) if wins else 0,
            "avg_loss": round(sum(losses) / len(losses), 2) if losses else 0,
            "profit_factor": round(abs(sum(wins) / sum(losses)), 2) if losses and sum(losses) != 0 else 0,
            "best_trade": round(max(pnls), 2),
            "worst_trade": round(min(pnls), 2),
            "by_strategy": by_strategy,
            "by_regime": by_regime,
            "by_pair": by_pair,
        }
