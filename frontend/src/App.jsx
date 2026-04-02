import React, { useState } from 'react';
import MarketOverview from './components/MarketOverview';
import SpreadChart from './components/SpreadChart';
import WeatherCorrelation from './components/WeatherCorrelation';
import BacktestPanel from './components/BacktestPanel';
import RiskDashboard from './components/RiskDashboard';

const TABS = ['Market Overview', 'Spread Analysis', 'Weather', 'Backtest', 'Risk'];
const ISOS = ['ERCOT', 'PJM', 'CAISO', 'MISO', 'NYISO', 'ISO-NE', 'SPP', 'IESO'];

const styles = {
  app: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    maxWidth: 1400,
    margin: '0 auto',
    padding: '20px',
    background: '#0a0a0f',
    color: '#e0e0e0',
    minHeight: '100vh',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
    borderBottom: '1px solid #333',
    paddingBottom: 15,
  },
  title: {
    fontSize: 24,
    fontWeight: 700,
    color: '#00d4ff',
  },
  controls: {
    display: 'flex',
    gap: 12,
    alignItems: 'center',
  },
  select: {
    background: '#1a1a2e',
    color: '#e0e0e0',
    border: '1px solid #333',
    padding: '8px 12px',
    borderRadius: 6,
    fontSize: 14,
  },
  tabs: {
    display: 'flex',
    gap: 4,
    marginBottom: 20,
  },
  tab: {
    padding: '10px 20px',
    border: 'none',
    borderRadius: '6px 6px 0 0',
    cursor: 'pointer',
    fontSize: 14,
    fontWeight: 500,
    transition: 'all 0.2s',
  },
  tabActive: {
    background: '#1a1a2e',
    color: '#00d4ff',
  },
  tabInactive: {
    background: 'transparent',
    color: '#888',
  },
};

export default function App() {
  const [activeTab, setActiveTab] = useState(0);
  const [isoA, setIsoA] = useState('ERCOT');
  const [isoB, setIsoB] = useState('PJM');
  const [days, setDays] = useState(365);

  return (
    <div style={styles.app}>
      <div style={styles.header}>
        <span style={styles.title}>Cross-ISO Power Spread Analyzer</span>
        <div style={styles.controls}>
          <label>Market A:</label>
          <select style={styles.select} value={isoA} onChange={(e) => setIsoA(e.target.value)}>
            {ISOS.map((iso) => <option key={iso} value={iso}>{iso}</option>)}
          </select>
          <label>Market B:</label>
          <select style={styles.select} value={isoB} onChange={(e) => setIsoB(e.target.value)}>
            {ISOS.map((iso) => <option key={iso} value={iso}>{iso}</option>)}
          </select>
          <label>Days:</label>
          <select style={styles.select} value={days} onChange={(e) => setDays(Number(e.target.value))}>
            {[30, 90, 180, 365, 730].map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
        </div>
      </div>

      <div style={styles.tabs}>
        {TABS.map((tab, i) => (
          <button
            key={tab}
            onClick={() => setActiveTab(i)}
            style={{
              ...styles.tab,
              ...(i === activeTab ? styles.tabActive : styles.tabInactive),
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 0 && <MarketOverview isoA={isoA} isoB={isoB} days={days} />}
      {activeTab === 1 && <SpreadChart isoA={isoA} isoB={isoB} days={days} />}
      {activeTab === 2 && <WeatherCorrelation isoA={isoA} isoB={isoB} days={days} />}
      {activeTab === 3 && <BacktestPanel isoA={isoA} isoB={isoB} days={days} />}
      {activeTab === 4 && <RiskDashboard isoA={isoA} isoB={isoB} days={days} />}
    </div>
  );
}
