"""
Transmission constraint mapping and geographic visualization data.
Provides congestion paths, flow data, and geographic coordinates
for inter-ISO transmission interfaces.
"""

import numpy as np
import pandas as pd


# Major inter-ISO transmission interfaces with geographic coordinates
TRANSMISSION_INTERFACES = {
    "ERCOT-SPP": {
        "name": "DC Ties (ERCOT-SPP)",
        "capacity_mw": 820,
        "from_coords": [31.0, -97.0],
        "to_coords": [35.5, -97.5],
        "description": "DC ties connecting ERCOT to SPP (limited capacity)",
    },
    "PJM-NYISO": {
        "name": "PJM-NYISO Interface",
        "capacity_mw": 4000,
        "from_coords": [40.2, -75.2],
        "to_coords": [41.0, -74.0],
        "description": "Multiple AC lines connecting PJM to NYISO",
    },
    "PJM-MISO": {
        "name": "PJM-MISO Interface",
        "capacity_mw": 5000,
        "from_coords": [40.0, -76.0],
        "to_coords": [41.9, -87.6],
        "description": "Major east-west AC interface",
    },
    "NYISO-ISO-NE": {
        "name": "Cross Sound Cable + AC Ties",
        "capacity_mw": 2400,
        "from_coords": [41.0, -74.0],
        "to_coords": [42.4, -71.1],
        "description": "Submarine cable and AC ties to New England",
    },
    "MISO-SPP": {
        "name": "MISO-SPP Interface",
        "capacity_mw": 3500,
        "from_coords": [41.9, -87.6],
        "to_coords": [35.5, -97.5],
        "description": "North-south interface through central US",
    },
    "CAISO-SPP": {
        "name": "CAISO-SPP Path",
        "capacity_mw": 1500,
        "from_coords": [34.1, -118.2],
        "to_coords": [35.5, -97.5],
        "description": "East-west path through desert southwest",
    },
    "MISO-PJM-NYISO": {
        "name": "West-to-East Corridor",
        "capacity_mw": 4000,
        "from_coords": [41.9, -87.6],
        "to_coords": [40.7, -74.0],
        "description": "Midwest to Northeast transmission corridor",
    },
    "IESO-NYISO": {
        "name": "Ontario-New York Interface",
        "capacity_mw": 2100,
        "from_coords": [43.7, -79.4],
        "to_coords": [41.0, -74.0],
        "description": "Cross-border AC ties",
    },
    "CAISO-PJM": {
        "name": "West-to-East (via SPP/MISO)",
        "capacity_mw": 1000,
        "from_coords": [34.1, -118.2],
        "to_coords": [40.0, -76.0],
        "description": "Long-haul path across multiple regions",
    },
    "ISO-NE-IESO": {
        "name": "New England-Ontario",
        "capacity_mw": 1400,
        "from_coords": [42.4, -71.1],
        "to_coords": [43.7, -79.4],
        "description": "Cross-border hydro import path",
    },
}

# ISO hub coordinates for map display
ISO_COORDINATES = {
    "ERCOT": {"lat": 31.0, "lon": -97.0, "city": "Austin"},
    "PJM": {"lat": 40.0, "lon": -76.0, "city": "Philadelphia"},
    "CAISO": {"lat": 34.1, "lon": -118.2, "city": "Los Angeles"},
    "MISO": {"lat": 41.9, "lon": -87.6, "city": "Chicago"},
    "NYISO": {"lat": 40.7, "lon": -74.0, "city": "New York"},
    "ISO-NE": {"lat": 42.4, "lon": -71.1, "city": "Boston"},
    "SPP": {"lat": 35.5, "lon": -97.5, "city": "Oklahoma City"},
    "IESO": {"lat": 43.7, "lon": -79.4, "city": "Toronto"},
}


class TransmissionMapper:
    """Generates transmission constraint and flow data for visualization."""

    def __init__(self):
        self.interfaces = TRANSMISSION_INTERFACES
        self.iso_coords = ISO_COORDINATES

    def get_interfaces(self) -> list:
        """Return all transmission interfaces with metadata."""
        result = []
        for key, intf in self.interfaces.items():
            result.append({
                "id": key,
                **intf,
            })
        return result

    def get_iso_nodes(self) -> list:
        """Return ISO hub locations for map display."""
        return [
            {"iso": iso, **coords}
            for iso, coords in self.iso_coords.items()
        ]

    def simulate_flows(self, congestion_data: pd.DataFrame = None) -> list:
        """
        Generate flow data for each interface.
        In production, this would come from real-time OASIS data.
        """
        np.random.seed(int(pd.Timestamp.now().timestamp()) % (2**31))
        flows = []

        for key, intf in self.interfaces.items():
            capacity = intf["capacity_mw"]
            # Simulate utilization (typically 40-90%)
            utilization = 0.4 + np.random.rand() * 0.5
            flow = capacity * utilization
            direction = 1 if np.random.rand() > 0.3 else -1

            # Congestion severity based on utilization
            if utilization > 0.85:
                congestion_level = "high"
                color = "#ff4444"
            elif utilization > 0.65:
                congestion_level = "medium"
                color = "#ffaa00"
            else:
                congestion_level = "low"
                color = "#44ff44"

            flows.append({
                "id": key,
                "name": intf["name"],
                "capacity_mw": capacity,
                "flow_mw": round(flow * direction, 0),
                "utilization_pct": round(utilization * 100, 1),
                "congestion_level": congestion_level,
                "color": color,
                "from_coords": intf["from_coords"],
                "to_coords": intf["to_coords"],
            })

        return flows

    def congestion_history(
        self, df_a: pd.DataFrame, df_b: pd.DataFrame, pair: str
    ) -> pd.DataFrame:
        """
        Historical congestion between two ISOs derived from price spreads.
        Large absolute spreads indicate transmission congestion.
        """
        daily_a = df_a.set_index("timestamp").resample("D")["congestion_component"].mean()
        daily_b = df_b.set_index("timestamp").resample("D")["congestion_component"].mean()

        combined = pd.DataFrame({
            "congestion_a": daily_a,
            "congestion_b": daily_b,
        }).dropna()

        combined["congestion_differential"] = combined["congestion_a"] - combined["congestion_b"]
        combined["abs_differential"] = combined["congestion_differential"].abs()

        # Classify congestion severity
        p75 = combined["abs_differential"].quantile(0.75)
        p95 = combined["abs_differential"].quantile(0.95)
        combined["severity"] = "low"
        combined.loc[combined["abs_differential"] > p75, "severity"] = "medium"
        combined.loc[combined["abs_differential"] > p95, "severity"] = "high"

        combined["pair"] = pair
        combined.index.name = "date"
        return combined.reset_index()
