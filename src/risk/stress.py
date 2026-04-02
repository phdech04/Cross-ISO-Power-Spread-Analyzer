"""
Scenario stress testing for power spread portfolios.
Models historical extreme events and hypothetical scenarios.
"""

import numpy as np
import pandas as pd


class StressTest:
    SCENARIOS = {
        "2021_texas_freeze": {
            "description": "Feb 2021 ERCOT crisis — prices hit $9,000/MWh for 4 days",
            "affected_isos": ["ERCOT"],
            "price_multiplier": {"ERCOT": 50.0},
            "spread_shock": {"ERCOT-PJM": 200.0, "ERCOT-MISO": 180.0},
            "duration_hours": 96,
            "volatility_multiplier": 10.0,
        },
        "2020_covid_demand_drop": {
            "description": "COVID demand destruction — 30% demand decline across all ISOs",
            "affected_isos": ["ERCOT", "PJM", "CAISO", "MISO", "NYISO", "ISO-NE", "SPP", "IESO"],
            "price_multiplier": {iso: 0.7 for iso in ["ERCOT", "PJM", "CAISO", "MISO", "NYISO", "ISO-NE", "SPP", "IESO"]},
            "spread_shock": {},
            "duration_hours": 720,  # ~30 days
            "volatility_multiplier": 3.0,
        },
        "heat_dome": {
            "description": "Pacific NW 2021-style heat dome — extreme temps in western ISOs",
            "affected_isos": ["CAISO", "SPP"],
            "price_multiplier": {"CAISO": 5.0, "SPP": 3.0},
            "spread_shock": {"CAISO-PJM": 80.0},
            "duration_hours": 168,  # 1 week
            "volatility_multiplier": 5.0,
        },
        "polar_vortex": {
            "description": "2014-style polar vortex — extreme cold across eastern ISOs",
            "affected_isos": ["PJM", "NYISO", "ISO-NE", "MISO"],
            "price_multiplier": {"PJM": 8.0, "NYISO": 10.0, "ISO-NE": 12.0, "MISO": 6.0},
            "spread_shock": {"NYISO-ERCOT": 150.0},
            "duration_hours": 120,
            "volatility_multiplier": 8.0,
        },
    }

    def run_scenario(
        self,
        scenario_name: str,
        current_positions: dict,
        position_size_mw: float = 50,
    ) -> dict:
        """
        Apply a stress scenario to current positions.

        current_positions: dict of spread_pair -> position_direction
            e.g. {"ERCOT-PJM": 1, "CAISO-MISO": -1}
            1 = long spread, -1 = short spread
        """
        scenario = self.SCENARIOS[scenario_name]
        results = {
            "scenario": scenario_name,
            "description": scenario["description"],
            "duration_hours": scenario["duration_hours"],
            "position_impacts": [],
            "total_pnl": 0.0,
        }

        for pair, direction in current_positions.items():
            shock = scenario.get("spread_shock", {}).get(pair, 0)
            pnl = direction * shock * position_size_mw * (scenario["duration_hours"] / 24)

            results["position_impacts"].append({
                "pair": pair,
                "direction": "long" if direction > 0 else "short",
                "spread_shock": shock,
                "estimated_pnl": pnl,
            })
            results["total_pnl"] += pnl

        results["total_pnl"] = float(results["total_pnl"])
        return results

    def run_all_scenarios(
        self, current_positions: dict, position_size_mw: float = 50
    ) -> pd.DataFrame:
        """Run all predefined stress scenarios."""
        results = []
        for name in self.SCENARIOS:
            r = self.run_scenario(name, current_positions, position_size_mw)
            results.append({
                "scenario": name,
                "description": r["description"],
                "total_pnl": r["total_pnl"],
                "duration_hours": r["duration_hours"],
            })
        return pd.DataFrame(results)

    def custom_scenario(
        self,
        spread_shocks: dict,
        current_positions: dict,
        position_size_mw: float = 50,
        duration_hours: int = 24,
    ) -> dict:
        """Run a custom stress scenario with user-defined shocks."""
        total_pnl = 0.0
        impacts = []

        for pair, direction in current_positions.items():
            shock = spread_shocks.get(pair, 0)
            pnl = direction * shock * position_size_mw * (duration_hours / 24)
            impacts.append({
                "pair": pair,
                "direction": "long" if direction > 0 else "short",
                "spread_shock": shock,
                "estimated_pnl": pnl,
            })
            total_pnl += pnl

        return {
            "scenario": "custom",
            "position_impacts": impacts,
            "total_pnl": float(total_pnl),
            "duration_hours": duration_hours,
        }
