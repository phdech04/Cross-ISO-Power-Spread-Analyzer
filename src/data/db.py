"""
DuckDB integration for power market data.
Runs locally, no server needed. Reads parquet natively.
"""

import logging
from pathlib import Path

import duckdb
import pandas as pd

logger = logging.getLogger(__name__)

SQL_DIR = Path(__file__).resolve().parent.parent.parent / "sql"


class PowerDB:
    def __init__(self, db_path: str = ":memory:"):
        self.conn = duckdb.connect(db_path)
        self._init_schema()

    def _init_schema(self):
        schema_path = SQL_DIR / "create_tables.sql"
        with open(schema_path) as f:
            self.conn.execute(f.read())

    def load_parquet(self, table: str, path: str):
        """Load a parquet file into a DuckDB table."""
        self.conn.execute(
            f"INSERT INTO {table} SELECT * FROM read_parquet('{path}')"
        )
        count = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        logger.info(f"Loaded {count} rows into {table} from {path}")

    def load_dataframe(self, table: str, df: pd.DataFrame):
        """Load a pandas DataFrame directly into a DuckDB table."""
        # DuckDB can query DataFrames as virtual tables
        self.conn.execute(f"INSERT INTO {table} SELECT * FROM df")
        count = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        logger.info(f"Loaded {count} rows into {table}")

    def daily_spreads(self, iso_a: str, iso_b: str) -> pd.DataFrame:
        """Compute daily spread between two ISOs."""
        query_path = SQL_DIR / "daily_spreads.sql"
        with open(query_path) as f:
            query = f.read()
        return self.conn.execute(query, [iso_a, iso_b]).fetchdf()

    def hourly_shape(self) -> pd.DataFrame:
        """Average hourly price shape by ISO and month."""
        query_path = SQL_DIR / "hourly_shape.sql"
        with open(query_path) as f:
            query = f.read()
        return self.conn.execute(query).fetchdf()

    def weather_join(self) -> pd.DataFrame:
        """Join weather and price data with lag features."""
        query_path = SQL_DIR / "weather_join.sql"
        with open(query_path) as f:
            query = f.read()
        return self.conn.execute(query).fetchdf()

    def query(self, sql: str, params: list = None) -> pd.DataFrame:
        """Run an arbitrary SQL query and return a DataFrame."""
        if params:
            return self.conn.execute(sql, params).fetchdf()
        return self.conn.execute(sql).fetchdf()

    def close(self):
        self.conn.close()
