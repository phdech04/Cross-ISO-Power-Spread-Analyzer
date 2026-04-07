"""
Congestion component analysis and FTR (Financial Transmission Rights) valuation.
Decomposes LMP into energy, congestion, and loss components to identify
transmission constraint-driven spread opportunities.
"""

import logging

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


class CongestionAnalyzer:
    """Analyzes LMP congestion components across ISOs."""

    def component_breakdown(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Daily breakdown of LMP into energy, congestion, and loss.
        Input: DataFrame with columns [timestamp, iso, lmp, energy_component,
               congestion_component, loss_component]
        """
        df = df.copy()
        df["date"] = pd.to_datetime(df["timestamp"]).dt.date

        daily = df.groupby(["iso", "date"]).agg({
            "lmp": "mean",
            "energy_component": "mean",
            "congestion_component": "mean",
            "loss_component": "mean",
        }).reset_index()

        # Component percentages
        daily["energy_pct"] = (daily["energy_component"] / daily["lmp"].replace(0, np.nan) * 100)
        daily["congestion_pct"] = (daily["congestion_component"] / daily["lmp"].replace(0, np.nan) * 100)
        daily["loss_pct"] = (daily["loss_component"] / daily["lmp"].replace(0, np.nan) * 100)

        return daily

    def congestion_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """Per-ISO congestion statistics."""
        results = []
        for iso, group in df.groupby("iso"):
            cong = group["congestion_component"].dropna()
            if len(cong) < 10:
                continue
            results.append({
                "iso": iso,
                "mean_congestion": round(float(cong.mean()), 2),
                "std_congestion": round(float(cong.std()), 2),
                "max_congestion": round(float(cong.max()), 2),
                "min_congestion": round(float(cong.min()), 2),
                "congestion_pct_of_lmp": round(
                    float(cong.mean() / group["lmp"].mean() * 100)
                    if group["lmp"].mean() != 0 else 0, 1
                ),
                "hours_above_5": int((cong.abs() > 5).sum()),
                "hours_above_10": int((cong.abs() > 10).sum()),
            })
        return pd.DataFrame(results)

    def congestion_spread(
        self, df_a: pd.DataFrame, df_b: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Compute congestion-driven spread between two ISOs.
        This isolates the transmission constraint component.
        """
        daily_a = (
            df_a.set_index("timestamp")
            .resample("D")
            .agg({"congestion_component": "mean", "energy_component": "mean", "lmp": "mean"})
            .rename(columns=lambda c: f"{c}_a")
        )
        daily_b = (
            df_b.set_index("timestamp")
            .resample("D")
            .agg({"congestion_component": "mean", "energy_component": "mean", "lmp": "mean"})
            .rename(columns=lambda c: f"{c}_b")
        )

        combined = pd.concat([daily_a, daily_b], axis=1).dropna()
        combined["total_spread"] = combined["lmp_a"] - combined["lmp_b"]
        combined["congestion_spread"] = (
            combined["congestion_component_a"] - combined["congestion_component_b"]
        )
        combined["energy_spread"] = (
            combined["energy_component_a"] - combined["energy_component_b"]
        )
        combined["congestion_contribution_pct"] = np.where(
            combined["total_spread"] != 0,
            combined["congestion_spread"] / combined["total_spread"] * 100,
            0,
        )

        combined.index.name = "trade_date"
        return combined.reset_index()

    def ftr_valuation(
        self, congestion_spread: pd.DataFrame, mw: float = 50
    ) -> dict:
        """
        Estimate FTR (Financial Transmission Right) value.
        FTR value = congestion spread * MW * hours
        """
        cong = congestion_spread["congestion_spread"].dropna()

        # Monthly FTR value estimate
        daily_value = cong * mw * 24  # $/day
        monthly_value = daily_value.rolling(30).sum()

        return {
            "avg_daily_congestion_spread": round(float(cong.mean()), 2),
            "avg_daily_ftr_value": round(float(daily_value.mean()), 2),
            "avg_monthly_ftr_value": round(float(monthly_value.dropna().mean()), 2),
            "annual_ftr_value_est": round(float(daily_value.mean() * 365), 2),
            "ftr_value_std": round(float(daily_value.std()), 2),
            "positive_days_pct": round(float((cong > 0).mean() * 100), 1),
            "mw_position": mw,
        }

    def hourly_congestion_pattern(self, df: pd.DataFrame) -> pd.DataFrame:
        """Average congestion by hour — identifies peak constraint hours."""
        df = df.copy()
        df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour
        return (
            df.groupby(["iso", "hour"])["congestion_component"]
            .agg(["mean", "std", "max"])
            .reset_index()
            .rename(columns={"mean": "avg_congestion", "std": "congestion_vol", "max": "peak_congestion"})
        )

    def seasonal_congestion(self, df: pd.DataFrame) -> pd.DataFrame:
        """Monthly congestion patterns — identifies seasonal constraints."""
        df = df.copy()
        df["month"] = pd.to_datetime(df["timestamp"]).dt.month
        return (
            df.groupby(["iso", "month"])["congestion_component"]
            .agg(["mean", "std", "max"])
            .reset_index()
            .rename(columns={"mean": "avg_congestion", "std": "congestion_vol", "max": "peak_congestion"})
        )

    def constraint_frequency(self, df: pd.DataFrame, threshold: float = 5.0) -> pd.DataFrame:
        """How often congestion exceeds threshold by ISO and hour."""
        df = df.copy()
        df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour
        df["constrained"] = df["congestion_component"].abs() > threshold

        freq = (
            df.groupby(["iso", "hour"])["constrained"]
            .mean()
            .reset_index()
            .rename(columns={"constrained": "constraint_frequency"})
        )
        freq["constraint_frequency"] = (freq["constraint_frequency"] * 100).round(1)
        return freq
