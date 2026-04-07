"""
Regulatory event calendar for power markets.
Tracks FERC filings, capacity auctions, planned outages,
and other events that affect spread dynamics.
"""

from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd


# Pre-populated event database
MARKET_EVENTS = [
    # Capacity auctions
    {
        "date": "2026-05-01",
        "end_date": "2026-05-15",
        "title": "PJM Base Residual Auction",
        "category": "capacity_auction",
        "isos": ["PJM"],
        "impact": "high",
        "description": "Annual capacity auction for delivery year 2029/2030. Clears capacity prices for the RTO.",
    },
    {
        "date": "2026-02-01",
        "end_date": "2026-02-10",
        "title": "ISO-NE Forward Capacity Auction",
        "category": "capacity_auction",
        "isos": ["ISO-NE"],
        "impact": "high",
        "description": "FCA for capacity commitment period beginning June 2029.",
    },
    {
        "date": "2026-04-15",
        "end_date": "2026-04-15",
        "title": "NYISO ICAP Spot Auction",
        "category": "capacity_auction",
        "isos": ["NYISO"],
        "impact": "medium",
        "description": "Monthly installed capacity spot auction.",
    },
    # FERC filings
    {
        "date": "2026-03-15",
        "end_date": "2026-03-15",
        "title": "FERC Order 2222 Compliance Filing",
        "category": "regulatory",
        "isos": ["PJM", "MISO", "CAISO", "NYISO", "ISO-NE", "SPP"],
        "impact": "medium",
        "description": "DER aggregation participation model compliance deadline.",
    },
    {
        "date": "2026-06-01",
        "end_date": "2026-06-01",
        "title": "ERCOT Market Redesign Phase 2",
        "category": "regulatory",
        "isos": ["ERCOT"],
        "impact": "high",
        "description": "Performance Credit Mechanism implementation following Winter Storm Uri reforms.",
    },
    {
        "date": "2026-07-01",
        "end_date": "2026-07-01",
        "title": "CAISO Extended Day-Ahead Market Go-Live",
        "category": "regulatory",
        "isos": ["CAISO", "SPP"],
        "impact": "high",
        "description": "EDAM launch expanding CAISO day-ahead market to western entities.",
    },
    # Seasonal events
    {
        "date": "2026-06-01",
        "end_date": "2026-09-30",
        "title": "ERCOT Summer Peak Season",
        "category": "seasonal",
        "isos": ["ERCOT"],
        "impact": "high",
        "description": "Summer demand peak period. Conservation appeals and emergency procedures possible above 80GW.",
    },
    {
        "date": "2026-12-01",
        "end_date": "2027-02-28",
        "title": "ISO-NE Winter Reliability Season",
        "category": "seasonal",
        "isos": ["ISO-NE"],
        "impact": "high",
        "description": "Gas pipeline constraints drive extreme price spikes. LNG import dependency peaks.",
    },
    {
        "date": "2026-04-01",
        "end_date": "2026-05-31",
        "title": "Spring Shoulder Maintenance Season",
        "category": "maintenance",
        "isos": ["PJM", "MISO", "NYISO"],
        "impact": "medium",
        "description": "Major generation units schedule planned outages during low-demand shoulder months.",
    },
    {
        "date": "2026-10-01",
        "end_date": "2026-11-15",
        "title": "Fall Shoulder Maintenance Season",
        "category": "maintenance",
        "isos": ["PJM", "MISO", "ERCOT"],
        "impact": "medium",
        "description": "Pre-winter maintenance window for thermal and nuclear fleet.",
    },
    # Transmission
    {
        "date": "2026-08-01",
        "end_date": "2026-08-01",
        "title": "MISO Long-Range Transmission Plan Tranche 2",
        "category": "transmission",
        "isos": ["MISO"],
        "impact": "medium",
        "description": "Board approval of $10B+ transmission expansion for renewable integration.",
    },
    {
        "date": "2026-09-15",
        "end_date": "2026-09-15",
        "title": "PJM Regional Transmission Expansion Plan",
        "category": "transmission",
        "isos": ["PJM"],
        "impact": "medium",
        "description": "Annual RTEP update with new project approvals for data center load growth.",
    },
    # Renewable milestones
    {
        "date": "2026-05-15",
        "end_date": "2026-05-15",
        "title": "ERCOT 40GW Wind Capacity Milestone",
        "category": "generation",
        "isos": ["ERCOT"],
        "impact": "medium",
        "description": "Installed wind capacity crosses 40GW threshold — increased negative price frequency.",
    },
    {
        "date": "2026-07-01",
        "end_date": "2026-07-01",
        "title": "CAISO Battery Storage 10GW Online",
        "category": "generation",
        "isos": ["CAISO"],
        "impact": "high",
        "description": "Battery storage mitigates duck curve — reduced evening ramp premium.",
    },
]


class EventCalendar:
    """Manages regulatory and market events for power markets."""

    def __init__(self):
        self.events = [self._parse_event(e) for e in MARKET_EVENTS]
        self.custom_events: List[dict] = []

    def _parse_event(self, event: dict) -> dict:
        event = event.copy()
        event["date"] = pd.Timestamp(event["date"])
        event["end_date"] = pd.Timestamp(event["end_date"])
        return event

    def get_events(
        self,
        start_date: str = None,
        end_date: str = None,
        iso: str = None,
        category: str = None,
    ) -> list:
        """Filter events by date range, ISO, and/or category."""
        events = self.events + self.custom_events

        if start_date:
            start = pd.Timestamp(start_date)
            events = [e for e in events if e["end_date"] >= start]
        if end_date:
            end = pd.Timestamp(end_date)
            events = [e for e in events if e["date"] <= end]
        if iso:
            events = [e for e in events if iso in e["isos"]]
        if category:
            events = [e for e in events if e["category"] == category]

        # Sort by date
        events.sort(key=lambda e: e["date"])

        return [
            {
                **e,
                "date": e["date"].strftime("%Y-%m-%d"),
                "end_date": e["end_date"].strftime("%Y-%m-%d"),
            }
            for e in events
        ]

    def get_upcoming(self, days: int = 90, iso: str = None) -> list:
        """Get events in the next N days."""
        now = pd.Timestamp.now().normalize()
        end = now + pd.Timedelta(days=days)
        return self.get_events(
            start_date=now.strftime("%Y-%m-%d"),
            end_date=end.strftime("%Y-%m-%d"),
            iso=iso,
        )

    def add_event(
        self,
        date: str,
        title: str,
        category: str,
        isos: list,
        impact: str = "medium",
        description: str = "",
        end_date: str = None,
    ):
        """Add a custom event to the calendar."""
        event = {
            "date": pd.Timestamp(date),
            "end_date": pd.Timestamp(end_date or date),
            "title": title,
            "category": category,
            "isos": isos,
            "impact": impact,
            "description": description,
        }
        self.custom_events.append(event)

    def get_categories(self) -> list:
        """Return all event categories."""
        cats = set()
        for e in self.events + self.custom_events:
            cats.add(e["category"])
        return sorted(cats)

    def events_for_pair(self, iso_a: str, iso_b: str, days: int = 90) -> list:
        """Get events affecting either ISO in a spread pair."""
        all_events = self.get_upcoming(days=days)
        return [
            e for e in all_events
            if iso_a in e["isos"] or iso_b in e["isos"]
        ]
