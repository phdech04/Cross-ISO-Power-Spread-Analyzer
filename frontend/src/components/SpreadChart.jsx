import React, { useEffect, useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, ReferenceLine,
} from 'recharts';
import { fetchSpread } from '../utils/api';

const cardStyle = {
  background: '#1a1a2e',
  borderRadius: 8,
  padding: 20,
  marginBottom: 20,
};

const statGrid = {
  display: 'grid',
  gridTemplateColumns: 'repeat(4, 1fr)',
  gap: 15,
  marginBottom: 20,
};

const statCard = {
  background: '#16213e',
  borderRadius: 8,
  padding: '12px 16px',
  textAlign: 'center',
};

export default function SpreadChart({ isoA, isoB, days }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchSpread(isoA, isoB, days)
      .then((d) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [isoA, isoB, days]);

  if (loading) return <div style={cardStyle}>Loading spread data...</div>;
  if (!data) return <div style={cardStyle}>Failed to load spread data.</div>;

  const stats = data.stats || {};
  const chartData = data.data.map((d) => ({
    ...d,
    date: d.date.slice(0, 10),
  }));

  return (
    <div>
      <div style={statGrid}>
        <div style={statCard}>
          <div style={{ color: '#888', fontSize: 12 }}>Mean Spread</div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>${(stats.mean || 0).toFixed(2)}</div>
        </div>
        <div style={statCard}>
          <div style={{ color: '#888', fontSize: 12 }}>Std Dev</div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>${(stats.std || 0).toFixed(2)}</div>
        </div>
        <div style={statCard}>
          <div style={{ color: '#888', fontSize: 12 }}>Half-Life</div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>{(stats.half_life || 0).toFixed(1)}d</div>
        </div>
        <div style={statCard}>
          <div style={{ color: '#888', fontSize: 12 }}>Hurst</div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>{(stats.hurst || 0).toFixed(3)}</div>
        </div>
      </div>

      <div style={cardStyle}>
        <h3 style={{ marginTop: 0 }}>Spread: {isoA} - {isoB}</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="date" stroke="#888" tick={{ fontSize: 11 }} />
            <YAxis stroke="#888" />
            <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid #333' }} />
            <ReferenceLine y={stats.mean || 0} stroke="#666" strokeDasharray="5 5" />
            <Line type="monotone" dataKey="spread" stroke="#51cf66" dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div style={cardStyle}>
        <h3 style={{ marginTop: 0 }}>Z-Score (20-day rolling)</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="date" stroke="#888" tick={{ fontSize: 11 }} />
            <YAxis stroke="#888" />
            <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid #333' }} />
            <ReferenceLine y={1.5} stroke="#ff6b6b" strokeDasharray="3 3" />
            <ReferenceLine y={-1.5} stroke="#ff6b6b" strokeDasharray="3 3" />
            <ReferenceLine y={0} stroke="#666" />
            <Line type="monotone" dataKey="zscore" stroke="#845ef7" dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
