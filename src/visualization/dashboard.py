"""
Streamlit dashboard for Cross-ISO Power Spread Analyzer.
Run with: streamlit run src/visualization/dashboard.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.data.fetcher import ISODataFetcher
from src.data.weather import WeatherFetcher
from src.data.processor import DataProcessor
from src.analysis.spreads import SpreadAnalyzer
from src.analysis.correlation import WeatherCorrelation
from src.analysis.seasonality import SeasonalityAnalyzer
from src.analysis.regime import RegimeDetector
from src.strategy.mean_reversion import MeanReversionStrategy
from src.strategy.momentum import MomentumStrategy
from src.strategy.backtest import BacktestEngine
from src.risk.var import RiskMetrics
from src.risk.stress import StressTest
from src.risk.position import PositionSizer

# ── Page Config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Power Spread Analyzer",
    page_icon="⚡",
    layout="wide",
)

st.title("Cross-ISO Power Spread Analyzer")

# ── Sidebar ──────────────────────────────────────────────────────────
st.sidebar.header("Configuration")

CONFIG_PATH = str(Path(__file__).resolve().parent.parent.parent / "config" / "settings.yaml")

ISOS = ["ERCOT", "PJM", "CAISO", "MISO", "NYISO", "ISO-NE", "SPP", "IESO"]

iso_a = st.sidebar.selectbox("Market A", ISOS, index=0)
iso_b = st.sidebar.selectbox("Market B", ISOS, index=1)

days = st.sidebar.slider("Lookback (days)", 30, 730, 365)

st.sidebar.subheader("Strategy Parameters")
lookback = st.sidebar.slider("Rolling Window", 5, 60, 20)
entry_z = st.sidebar.slider("Entry Z-Score", 0.5, 3.0, 1.5, 0.1)
exit_z = st.sidebar.slider("Exit Z-Score", 0.0, 1.5, 0.3, 0.1)
stop_z = st.sidebar.slider("Stop Loss Z-Score", 2.0, 5.0, 3.0, 0.1)


# ── Data Loading ─────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_data(iso_a, iso_b, days):
    fetcher = ISODataFetcher(config_path=CONFIG_PATH)
    end_date = pd.Timestamp.now().strftime("%Y-%m-%d")
    start_date = (pd.Timestamp.now() - pd.Timedelta(days=days)).strftime("%Y-%m-%d")

    df_a = fetcher.fetch(iso_a, start_date, end_date)
    df_b = fetcher.fetch(iso_b, start_date, end_date)
    return df_a, df_b, start_date, end_date


@st.cache_data(ttl=3600)
def load_weather(days):
    weather = WeatherFetcher(config_path=CONFIG_PATH)
    end_date = pd.Timestamp.now().strftime("%Y-%m-%d")
    start_date = (pd.Timestamp.now() - pd.Timedelta(days=days)).strftime("%Y-%m-%d")
    return weather.fetch_all(start_date, end_date)


df_a, df_b, start_date, end_date = load_data(iso_a, iso_b, days)

# ── Tabs ─────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Market Overview", "Spread Analysis",
    "Weather Correlation", "Backtest", "Risk",
])

# ── Tab 1: Market Overview ───────────────────────────────────────────
with tab1:
    st.header("Market Overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(f"{iso_a} Avg Price", f"${df_a['lmp'].mean():.2f}/MWh")
    col2.metric(f"{iso_b} Avg Price", f"${df_b['lmp'].mean():.2f}/MWh")
    col3.metric(f"{iso_a} Volatility", f"${df_a['lmp'].std():.2f}")
    col4.metric(f"{iso_b} Volatility", f"${df_b['lmp'].std():.2f}")

    # Daily prices
    daily_a = df_a.set_index("timestamp").resample("D")["lmp"].mean().reset_index()
    daily_a["iso"] = iso_a
    daily_b = df_b.set_index("timestamp").resample("D")["lmp"].mean().reset_index()
    daily_b["iso"] = iso_b
    daily_both = pd.concat([daily_a, daily_b])

    fig = px.line(daily_both, x="timestamp", y="lmp", color="iso",
                  title="Daily Average LMP", labels={"lmp": "$/MWh"})
    st.plotly_chart(fig, use_container_width=True)

    # Hourly shape
    df_a_copy = df_a.copy()
    df_b_copy = df_b.copy()
    df_a_copy["hour"] = df_a_copy["timestamp"].dt.hour
    df_b_copy["hour"] = df_b_copy["timestamp"].dt.hour
    df_a_copy["iso"] = iso_a
    df_b_copy["iso"] = iso_b
    hourly = pd.concat([df_a_copy, df_b_copy])
    hourly_avg = hourly.groupby(["hour", "iso"])["lmp"].mean().reset_index()

    fig2 = px.line(hourly_avg, x="hour", y="lmp", color="iso",
                   title="Avg Hourly Price Shape", labels={"lmp": "$/MWh"})
    st.plotly_chart(fig2, use_container_width=True)

# ── Tab 2: Spread Analysis ──────────────────────────────────────────
with tab2:
    st.header(f"Spread Analysis: {iso_a} vs {iso_b}")

    analyzer = SpreadAnalyzer()
    spread_df = analyzer.compute_spread(df_a, df_b)
    spreads = spread_df["spread"]

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Mean Spread", f"${spreads.mean():.2f}")
    col2.metric("Spread Vol", f"${spreads.std():.2f}")

    hl = analyzer.half_life(spreads)
    col3.metric("Half-Life", f"{hl:.1f} days")

    hurst = analyzer.hurst_exponent(spreads)
    col4.metric("Hurst Exponent", f"{hurst:.3f}")

    # Spread + Z-Score chart
    zscore = analyzer.rolling_zscore(spreads, window=lookback)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        subplot_titles=["Spread", "Z-Score"])
    fig.add_trace(go.Scatter(x=spread_df["trade_date"], y=spreads,
                             name="Spread"), row=1, col=1)
    fig.add_hline(y=spreads.mean(), line_dash="dash", row=1, col=1)

    fig.add_trace(go.Scatter(x=spread_df["trade_date"], y=zscore,
                             name="Z-Score"), row=2, col=1)
    fig.add_hline(y=entry_z, line_dash="dot", line_color="red", row=2, col=1)
    fig.add_hline(y=-entry_z, line_dash="dot", line_color="red", row=2, col=1)
    fig.add_hline(y=0, line_dash="dash", row=2, col=1)

    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)

    # Cointegration test
    coint = analyzer.cointegration_test(
        spread_df["price_a"].values, spread_df["price_b"].values
    )
    st.subheader("Cointegration Test")
    st.json(coint)

# ── Tab 3: Weather Correlation ───────────────────────────────────────
with tab3:
    st.header("Weather-Price Correlation")

    try:
        weather_data = load_weather(days)
        all_prices = pd.concat([df_a, df_b])
        processor = DataProcessor(config_path=CONFIG_PATH)
        merged = processor.merge_price_weather(all_prices, weather_data)

        corr = WeatherCorrelation()
        pearson = corr.pearson_by_iso(merged)
        st.subheader("Temperature-Price Correlation")
        st.dataframe(pearson)

        temp_response = corr.nonlinear_temp_response(merged)
        if len(temp_response) > 0:
            fig = px.scatter(temp_response, x="temp_mid", y="mean", color="iso",
                             title="V-Shaped Temperature Response",
                             labels={"temp_mid": "Temperature (°C)", "mean": "Avg LMP"})
            st.plotly_chart(fig, use_container_width=True)

        renewable = corr.wind_solar_impact(merged)
        st.subheader("Renewable Impact")
        st.dataframe(renewable)

    except Exception as e:
        st.warning(f"Weather data unavailable: {e}")

# ── Tab 4: Backtest ──────────────────────────────────────────────────
with tab4:
    st.header("Strategy Backtest")

    strategy_type = st.selectbox("Strategy", ["Mean Reversion", "Momentum"])

    if strategy_type == "Mean Reversion":
        strategy = MeanReversionStrategy(
            lookback=lookback, entry_z=entry_z,
            exit_z=exit_z, stop_loss_z=stop_z,
        )
    else:
        fast = st.number_input("Fast Window", value=5)
        slow = st.number_input("Slow Window", value=20)
        strategy = MomentumStrategy(fast_window=fast, slow_window=slow)

    signals = strategy.generate_signals(spreads)
    engine = BacktestEngine()
    result = engine.run(signals)

    # Metrics
    m = result["metrics"]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Return", f"{m['total_return_pct']:.1f}%")
    col2.metric("Sharpe Ratio", f"{m['sharpe_ratio']:.2f}")
    col3.metric("Max Drawdown", f"{m['max_drawdown_pct']:.1f}%")
    col4.metric("Win Rate", f"{m['win_rate']:.1%}")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Trades", m["n_trades"])
    col6.metric("Profit Factor", f"{m['profit_factor']:.2f}")
    col7.metric("Sortino", f"{m['sortino_ratio']:.2f}")
    col8.metric("Calmar", f"{m['calmar_ratio']:.2f}")

    # Equity curve
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=result["equity_curve"], name="Equity",
                             fill="tozeroy"))
    fig.update_layout(title="Equity Curve", yaxis_title="$",
                      height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Trade distribution
    if result["trade_pnl"]:
        fig2 = px.histogram(x=result["trade_pnl"], nbins=30,
                            title="Trade P&L Distribution",
                            labels={"x": "P&L ($)"})
        st.plotly_chart(fig2, use_container_width=True)

# ── Tab 5: Risk ──────────────────────────────────────────────────────
with tab5:
    st.header("Risk Analysis")

    risk = RiskMetrics()
    returns = result["daily_pnl"][1:] / 100_000

    report = risk.risk_report(returns, result["equity_curve"])

    col1, col2, col3 = st.columns(3)
    col1.metric("VaR 95%", f"{report['historical_var_95']:.4f}")
    col2.metric("CVaR 95%", f"{report['cvar_95']:.4f}")
    col3.metric("Annual Vol", f"{report['volatility_annual']:.4f}")

    # Stress testing
    st.subheader("Stress Scenarios")
    stress = StressTest()
    positions = {f"{iso_a}-{iso_b}": 1}
    stress_results = stress.run_all_scenarios(positions)
    st.dataframe(stress_results)

    # Position sizing
    st.subheader("Position Sizing")
    sizer = PositionSizer()
    sizing = sizer.optimal_size(
        capital=100_000,
        win_rate=m["win_rate"],
        avg_win=m["avg_win"],
        avg_loss=m["avg_loss"],
        max_risk_pct=0.02,
        stop_distance=5.0,
    )
    st.json(sizing)
