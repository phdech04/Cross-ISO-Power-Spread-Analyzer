"""
Weather data pipeline via Open-Meteo API.
Free, no API key needed. Provides historical hourly weather data.
"""

import logging
from pathlib import Path

import pandas as pd
import requests
import yaml

logger = logging.getLogger(__name__)


class WeatherFetcher:
    BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

    def __init__(self, config_path: str = "config/settings.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        self.locations = self.config["weather"]["locations"]
        self.cache_dir = Path(self.config["data"]["cache_dir"])
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch(self, lat: float, lon: float, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch hourly temperature, wind speed, solar radiation, humidity."""
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": (
                "temperature_2m,wind_speed_10m,"
                "direct_radiation,relative_humidity_2m"
            ),
            "timezone": "auto",
        }
        resp = requests.get(self.BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        hourly = data["hourly"]
        df = pd.DataFrame({
            "timestamp": pd.to_datetime(hourly["time"], utc=True),
            "temp_c": hourly["temperature_2m"],
            "wind_speed": hourly["wind_speed_10m"],
            "solar_radiation": hourly["direct_radiation"],
            "humidity": hourly["relative_humidity_2m"],
        })

        # Compute heating and cooling degree days (base 18°C)
        df["hdd"] = (18.0 - df["temp_c"]).clip(lower=0)
        df["cdd"] = (df["temp_c"] - 18.0).clip(lower=0)

        return df

    def fetch_for_iso(self, iso: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch weather for a specific ISO's representative location."""
        cache_path = self.cache_dir / f"weather_{iso}_{start_date}_{end_date}.parquet"
        if cache_path.exists():
            logger.info(f"Loading cached weather for {iso}")
            return pd.read_parquet(cache_path)

        location = self.locations[iso]
        lat, lon = location["lat"], location["lon"]

        try:
            df = self.fetch(lat, lon, start_date, end_date)
            df["iso"] = iso
            df["city"] = location.get("city", "")

            # Cache
            df.to_parquet(cache_path, index=False)
            logger.info(f"Fetched weather for {iso} ({location.get('city', '')}): {len(df)} rows")
            return df

        except Exception as e:
            logger.warning(f"Weather fetch failed for {iso}: {e}")
            return self._generate_synthetic_weather(iso, start_date, end_date)

    def _generate_synthetic_weather(
        self, iso: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """Synthetic weather fallback with realistic seasonal patterns."""
        import numpy as np

        np.random.seed(hash(f"weather_{iso}") % (2**31))

        start = pd.Timestamp(start_date, tz="UTC")
        end = pd.Timestamp(end_date, tz="UTC")
        timestamps = pd.date_range(start, end, freq="h")
        n = len(timestamps)

        day_of_year = timestamps.dayofyear.values
        hour = timestamps.hour.values

        # Base temperature patterns by region
        region_temps = {
            "ERCOT": {"mean": 22, "amp": 12, "phase": 200},
            "PJM": {"mean": 13, "amp": 14, "phase": 200},
            "CAISO": {"mean": 18, "amp": 6, "phase": 210},
            "MISO": {"mean": 10, "amp": 18, "phase": 195},
            "NYISO": {"mean": 12, "amp": 15, "phase": 200},
            "ISO-NE": {"mean": 10, "amp": 16, "phase": 200},
            "SPP": {"mean": 16, "amp": 14, "phase": 200},
            "IESO": {"mean": 7, "amp": 18, "phase": 195},
        }

        tp = region_temps.get(iso, {"mean": 15, "amp": 12, "phase": 200})

        # Seasonal + diurnal temperature
        seasonal = tp["amp"] * np.sin(2 * np.pi * (day_of_year - tp["phase"] + 80) / 365)
        diurnal = 4 * np.sin(2 * np.pi * (hour - 6) / 24)
        noise = np.random.randn(n) * 3
        temp_c = tp["mean"] + seasonal + diurnal + noise

        # Wind speed (Weibull-ish)
        base_wind = 3.5 if iso in ("SPP", "ERCOT", "MISO") else 2.5
        wind_speed = np.abs(np.random.weibull(2.0, n) * base_wind + 1)

        # Solar radiation (zero at night, peak midday)
        solar_base = 400 if iso == "CAISO" else 300
        solar = np.where(
            (hour >= 6) & (hour <= 18),
            solar_base * np.sin(np.pi * (hour - 6) / 12) * (1 + 0.2 * np.random.randn(n)),
            0,
        )
        solar = np.maximum(solar, 0)

        humidity = 60 + 15 * np.sin(2 * np.pi * (day_of_year - 100) / 365) + np.random.randn(n) * 8
        humidity = np.clip(humidity, 10, 100)

        df = pd.DataFrame({
            "timestamp": timestamps,
            "temp_c": np.round(temp_c, 1),
            "wind_speed": np.round(wind_speed, 1),
            "solar_radiation": np.round(solar, 2),
            "humidity": np.round(humidity, 1),
            "hdd": np.round(np.maximum(18.0 - temp_c, 0), 1),
            "cdd": np.round(np.maximum(temp_c - 18.0, 0), 1),
            "iso": iso,
            "city": self.locations.get(iso, {}).get("city", ""),
        })

        return df

    def fetch_all(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch weather data for all configured ISOs."""
        frames = []
        for iso in self.locations:
            df = self.fetch_for_iso(iso, start_date, end_date)
            frames.append(df)
        return pd.concat(frames, ignore_index=True)
