"""
Data processor: clean, align timezones, merge price + weather datasets,
and compute derived features for analysis.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

logger = logging.getLogger(__name__)


class DataProcessor:
    def __init__(self, config_path: str = "config/settings.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        self.peak_start = self.config["analysis"]["peak_hours"]["start"]
        self.peak_end = self.config["analysis"]["peak_hours"]["end"]
        self.processed_dir = Path(self.config["data"]["processed_dir"])
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def align_timezones(self, df: pd.DataFrame, tz_col: str = None) -> pd.DataFrame:
        """Convert all timestamps to UTC for cross-ISO comparison."""
        df = df.copy()
        if df["timestamp"].dt.tz is None:
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        else:
            df["timestamp"] = df["timestamp"].dt.tz_convert("UTC")
        return df

    def merge_price_weather(
        self, price_df: pd.DataFrame, weather_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Inner join on timestamp and ISO, forward-fill weather gaps."""
        price_df = self.align_timezones(price_df)
        weather_df = self.align_timezones(weather_df)

        # Truncate both to hourly for clean join
        price_df["timestamp"] = price_df["timestamp"].dt.floor("h")
        weather_df["timestamp"] = weather_df["timestamp"].dt.floor("h")

        # Drop duplicate columns before merge
        weather_cols = ["timestamp", "iso", "temp_c", "wind_speed",
                        "solar_radiation", "humidity", "hdd", "cdd"]
        weather_subset = weather_df[[c for c in weather_cols if c in weather_df.columns]]

        merged = pd.merge(
            price_df, weather_subset,
            on=["timestamp", "iso"],
            how="left",
        )

        # Forward-fill weather gaps (weather stations may have holes)
        weather_fields = ["temp_c", "wind_speed", "solar_radiation", "humidity", "hdd", "cdd"]
        for col in weather_fields:
            if col in merged.columns:
                merged[col] = merged.groupby("iso")[col].ffill()

        return merged

    def compute_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add derived columns for analysis:
        - Temporal: hour_of_day, day_of_week, month, is_peak, is_weekend
        - Weather: temp_deviation, heating/cooling degree days
        - Lagged: prices at 1h, 24h, 168h (1 week) ago
        - Rolling: 24h rolling mean and std
        """
        df = df.copy()

        # Temporal features
        df["hour_of_day"] = df["timestamp"].dt.hour
        df["day_of_week"] = df["timestamp"].dt.dayofweek
        df["month"] = df["timestamp"].dt.month
        df["day_of_year"] = df["timestamp"].dt.dayofyear
        df["is_peak"] = df["hour_of_day"].between(self.peak_start, self.peak_end)
        df["is_weekend"] = df["day_of_week"] >= 5

        # Temperature deviation from 30-day rolling mean
        if "temp_c" in df.columns:
            df["temp_30d_mean"] = (
                df.groupby("iso")["temp_c"]
                .transform(lambda x: x.rolling(720, min_periods=24).mean())
            )
            df["temp_deviation"] = df["temp_c"] - df["temp_30d_mean"]

        # Lagged prices
        for lag_hours, label in [(1, "1h"), (24, "24h"), (168, "168h")]:
            df[f"lmp_lag_{label}"] = df.groupby("iso")["lmp"].shift(lag_hours)

        # Price changes
        df["lmp_change_1h"] = df["lmp"] - df["lmp_lag_1h"]
        df["lmp_change_24h"] = df["lmp"] - df["lmp_lag_24h"]

        # Rolling statistics (24h window)
        df["lmp_rolling_24h_mean"] = (
            df.groupby("iso")["lmp"]
            .transform(lambda x: x.rolling(24, min_periods=1).mean())
        )
        df["lmp_rolling_24h_std"] = (
            df.groupby("iso")["lmp"]
            .transform(lambda x: x.rolling(24, min_periods=1).std())
        )

        # Log returns (for regime detection)
        df["lmp_return"] = df.groupby("iso")["lmp"].pct_change()

        return df

    def save_parquet(self, df: pd.DataFrame, name: str):
        """Save processed dataframe to parquet."""
        path = self.processed_dir / f"{name}.parquet"
        df.to_parquet(path, index=False)
        logger.info(f"Saved {len(df)} rows to {path}")
        return path

    def load_parquet(self, name: str) -> pd.DataFrame:
        """Load processed dataframe from parquet."""
        path = self.processed_dir / f"{name}.parquet"
        return pd.read_parquet(path)

    def run_pipeline(
        self, price_df: pd.DataFrame, weather_df: pd.DataFrame, save_name: str = "merged"
    ) -> pd.DataFrame:
        """Full pipeline: merge, compute features, save."""
        logger.info("Merging price and weather data...")
        merged = self.merge_price_weather(price_df, weather_df)

        logger.info("Computing features...")
        featured = self.compute_features(merged)

        logger.info(f"Pipeline complete: {len(featured)} rows, {len(featured.columns)} columns")
        self.save_parquet(featured, save_name)

        return featured
