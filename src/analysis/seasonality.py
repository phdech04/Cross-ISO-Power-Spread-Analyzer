"""
Seasonality decomposition: hourly shapes, monthly patterns,
weekday effects, and peak/off-peak analysis.
"""

import numpy as np
import pandas as pd


class SeasonalityAnalyzer:
    def hourly_shape(self, hourly_df: pd.DataFrame) -> pd.DataFrame:
        """Average price by hour — the classic load shape curve."""
        hourly_df = hourly_df.copy()
        hourly_df["hour"] = hourly_df["timestamp"].dt.hour
        return (
            hourly_df.groupby(["iso", "hour"])["lmp"]
            .agg(["mean", "std", "median", "count"])
            .reset_index()
            .rename(columns={"mean": "avg_price", "std": "price_vol",
                             "median": "median_price", "count": "obs"})
        )

    def monthly_pattern(self, daily_df: pd.DataFrame) -> pd.DataFrame:
        """Seasonal price pattern by month."""
        daily_df = daily_df.copy()
        daily_df["month"] = daily_df["timestamp"].dt.month
        return (
            daily_df.groupby(["iso", "month"])["lmp"]
            .agg(["mean", "std", "median"])
            .reset_index()
            .rename(columns={"mean": "avg_price", "std": "price_vol",
                             "median": "median_price"})
        )

    def weekday_effect(self, daily_df: pd.DataFrame) -> pd.DataFrame:
        """Weekend discount quantification."""
        daily_df = daily_df.copy()
        daily_df["day_of_week"] = daily_df["timestamp"].dt.dayofweek
        daily_df["day_name"] = daily_df["timestamp"].dt.day_name()
        daily_df["is_weekend"] = daily_df["day_of_week"] >= 5

        result = (
            daily_df.groupby(["iso", "day_of_week", "day_name"])["lmp"]
            .agg(["mean", "std"])
            .reset_index()
            .rename(columns={"mean": "avg_price", "std": "price_vol"})
        )

        # Compute weekend discount per ISO
        summary = []
        for iso, group in daily_df.groupby("iso"):
            weekday_avg = group[~group["is_weekend"]]["lmp"].mean()
            weekend_avg = group[group["is_weekend"]]["lmp"].mean()
            discount = weekend_avg - weekday_avg
            discount_pct = (discount / weekday_avg * 100) if weekday_avg != 0 else 0
            summary.append({
                "iso": iso,
                "weekday_avg": weekday_avg,
                "weekend_avg": weekend_avg,
                "weekend_discount": discount,
                "weekend_discount_pct": discount_pct,
            })

        return {
            "daily": result,
            "summary": pd.DataFrame(summary),
        }

    def peak_offpeak_ratio(
        self, hourly_df: pd.DataFrame, peak_start: int = 7, peak_end: int = 22
    ) -> pd.DataFrame:
        """
        On-peak vs off-peak ratio.
        Key trading metric — energy firms trade peak/offpeak spreads.
        """
        hourly_df = hourly_df.copy()
        hourly_df["hour"] = hourly_df["timestamp"].dt.hour
        hourly_df["is_peak"] = hourly_df["hour"].between(peak_start, peak_end)
        hourly_df["date"] = hourly_df["timestamp"].dt.date

        daily = hourly_df.groupby(["iso", "date", "is_peak"])["lmp"].mean().unstack()
        daily.columns = ["offpeak", "onpeak"]

        daily["peak_offpeak_spread"] = daily["onpeak"] - daily["offpeak"]
        daily["peak_offpeak_ratio"] = daily["onpeak"] / daily["offpeak"].replace(0, np.nan)

        return daily.reset_index()

    def decompose(self, hourly_df: pd.DataFrame) -> dict:
        """Run all seasonality analyses."""
        return {
            "hourly_shape": self.hourly_shape(hourly_df),
            "monthly_pattern": self.monthly_pattern(hourly_df),
            "weekday_effect": self.weekday_effect(hourly_df),
            "peak_offpeak": self.peak_offpeak_ratio(hourly_df),
        }
