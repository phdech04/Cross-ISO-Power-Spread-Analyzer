import React, { useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { runBacktest } from '../utils/api';

const cardStyle = {
  background: '#1a1a2e',
  borderRadius: 8,
  padding: 20,
  marginBottom: 20,
};

const metricGrid = {
  display: 'grid',
  gridTemplateColumns: 'repeat(4, 1fr)',
  gap: 12,
  marginBottom: 20,
};

const metricCard = {
  background: '#16213e',
  borderRadius: 8,
  padding: '12px 16px',
  textAlign: 'center',
};

const inputStyle = {
  background: '#16213e',
  color: '#e0e0e0',
  border: '1px solid #333',
  padding: '6px 10px',
  borderRadius: 4,
  width: 70,
};

const btnStyle = {
  background: '#00d4ff',
  color: '#000',
  border: 'none',
  padding: '10px 24px',
  borderRadius: 6,
  cursor: 'pointer',
  fontWeight: 600,
  fontSize: 14,
};

export default function BacktestPanel({ isoA, isoB, days }) {
  const [params, setParams] = useState({
    lookback: 20, entry_z: 1.5, exit_z: 0.3, stop_z: 3.0,
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleRun = () => {
    setLoading(true);
    runBacktest({
      iso_a: isoA, iso_b: isoB, days,
      strategy: 'mean_reversion',
      ...params,
    })
      .then((r) => { setResult(r); setLoading(false); })
      .catch(() => setLoading(false));
  };

  const m = result?.metrics || {};
  const equityCurve = (result?.equity_curve || []).map((v, i) => ({
    idx: i, equity: v,
  }));

  return (
    <div>
      <div style={cardStyle}>
        <h3 style={{ marginTop: 0 }}>Strategy Parameters</h3>
        <div style={{ display: 'flex', gap: 20, alignItems: 'center', flexWrap: 'wrap' }}>
          {Object.entries(params).map(([key, val]) => (
            <label key={key} style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              {key.replace('_', ' ')}:
              <input
                style={inputStyle}
                type="number"
                step={key === 'lookback' ? 1 : 0.1}
                value={val}
                onChange={(e) => setParams({ ...params, [key]: Number(e.target.value) })}
              />
            </label>
          ))}
          <button style={btnStyle} onClick={handleRun} disabled={loading}>
            {loading ? 'Running...' : 'Run Backtest'}
          </button>
        </div>
      </div>

      {result && (
        <>
          <div style={metricGrid}>
            <div style={metricCard}>
              <div style={{ color: '#888', fontSize: 12 }}>Total Return</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: m.total_return >= 0 ? '#51cf66' : '#ff6b6b' }}>
                {(m.total_return_pct || 0).toFixed(1)}%
              </div>
            </div>
            <div style={metricCard}>
              <div style={{ color: '#888', fontSize: 12 }}>Sharpe Ratio</div>
              <div style={{ fontSize: 20, fontWeight: 700 }}>{(m.sharpe_ratio || 0).toFixed(2)}</div>
            </div>
            <div style={metricCard}>
              <div style={{ color: '#888', fontSize: 12 }}>Max Drawdown</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: '#ff6b6b' }}>
                {(m.max_drawdown_pct || 0).toFixed(1)}%
              </div>
            </div>
            <div style={metricCard}>
              <div style={{ color: '#888', fontSize: 12 }}>Win Rate</div>
              <div style={{ fontSize: 20, fontWeight: 700 }}>
                {((m.win_rate || 0) * 100).toFixed(0)}%
              </div>
            </div>
          </div>

          <div style={cardStyle}>
            <h3 style={{ marginTop: 0 }}>Equity Curve</h3>
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={equityCurve}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="idx" stroke="#888" />
                <YAxis stroke="#888" domain={['auto', 'auto']} />
                <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid #333' }} />
                <Line type="monotone" dataKey="equity" stroke="#51cf66" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}
