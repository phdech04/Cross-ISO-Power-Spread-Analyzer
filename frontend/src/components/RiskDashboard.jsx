import React, { useEffect, useState } from 'react';
import { fetchRisk } from '../utils/api';

const cardStyle = {
  background: '#1a1a2e',
  borderRadius: 8,
  padding: 20,
  marginBottom: 20,
};

const metricGrid = {
  display: 'grid',
  gridTemplateColumns: 'repeat(3, 1fr)',
  gap: 12,
  marginBottom: 20,
};

const metricCard = {
  background: '#16213e',
  borderRadius: 8,
  padding: '12px 16px',
  textAlign: 'center',
};

const tableStyle = {
  width: '100%',
  borderCollapse: 'collapse',
  fontSize: 14,
};

const thStyle = {
  textAlign: 'left',
  padding: '10px 12px',
  borderBottom: '1px solid #333',
  color: '#888',
};

const tdStyle = {
  padding: '10px 12px',
  borderBottom: '1px solid #222',
};

export default function RiskDashboard({ isoA, isoB, days }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchRisk(isoA, isoB, days)
      .then((d) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [isoA, isoB, days]);

  if (loading) return <div style={cardStyle}>Loading risk analysis...</div>;
  if (!data) return <div style={cardStyle}>Failed to load risk data.</div>;

  const r = data.risk_report || {};
  const dd = r.drawdown || {};

  return (
    <div>
      <div style={metricGrid}>
        <div style={metricCard}>
          <div style={{ color: '#888', fontSize: 12 }}>VaR 95%</div>
          <div style={{ fontSize: 20, fontWeight: 700, color: '#ff6b6b' }}>
            {((r.historical_var_95 || 0) * 100).toFixed(2)}%
          </div>
        </div>
        <div style={metricCard}>
          <div style={{ color: '#888', fontSize: 12 }}>CVaR 95%</div>
          <div style={{ fontSize: 20, fontWeight: 700, color: '#ff6b6b' }}>
            {((r.cvar_95 || 0) * 100).toFixed(2)}%
          </div>
        </div>
        <div style={metricCard}>
          <div style={{ color: '#888', fontSize: 12 }}>Max Drawdown</div>
          <div style={{ fontSize: 20, fontWeight: 700, color: '#ff6b6b' }}>
            {(dd.max_drawdown_pct || 0).toFixed(1)}%
          </div>
        </div>
      </div>

      <div style={metricGrid}>
        <div style={metricCard}>
          <div style={{ color: '#888', fontSize: 12 }}>Annual Volatility</div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>
            {((r.volatility_annual || 0) * 100).toFixed(1)}%
          </div>
        </div>
        <div style={metricCard}>
          <div style={{ color: '#888', fontSize: 12 }}>Skewness</div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>{(r.skewness || 0).toFixed(3)}</div>
        </div>
        <div style={metricCard}>
          <div style={{ color: '#888', fontSize: 12 }}>Kurtosis</div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>{(r.kurtosis || 0).toFixed(3)}</div>
        </div>
      </div>

      <div style={cardStyle}>
        <h3 style={{ marginTop: 0 }}>Stress Scenarios</h3>
        <table style={tableStyle}>
          <thead>
            <tr>
              <th style={thStyle}>Scenario</th>
              <th style={thStyle}>Description</th>
              <th style={thStyle}>Duration</th>
              <th style={thStyle}>Est. P&L</th>
            </tr>
          </thead>
          <tbody>
            {(data.stress_tests || []).map((s, i) => (
              <tr key={i}>
                <td style={tdStyle}>{s.scenario}</td>
                <td style={tdStyle}>{s.description}</td>
                <td style={tdStyle}>{s.duration_hours}h</td>
                <td style={{
                  ...tdStyle,
                  color: s.total_pnl >= 0 ? '#51cf66' : '#ff6b6b',
                  fontWeight: 600,
                }}>
                  ${(s.total_pnl || 0).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
