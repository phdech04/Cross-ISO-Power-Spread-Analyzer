import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { fetchPrices } from '../utils/api';

const cardStyle = {
  background: '#1a1a2e',
  borderRadius: 8,
  padding: 20,
  marginBottom: 20,
};

const metricStyle = {
  display: 'flex',
  gap: 20,
  marginBottom: 20,
};

const metricCard = {
  background: '#16213e',
  borderRadius: 8,
  padding: '15px 20px',
  flex: 1,
  textAlign: 'center',
};

export default function MarketOverview({ isoA, isoB, days }) {
  const [dataA, setDataA] = useState(null);
  const [dataB, setDataB] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchPrices(isoA, days), fetchPrices(isoB, days)])
      .then(([a, b]) => {
        setDataA(a);
        setDataB(b);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [isoA, isoB, days]);

  if (loading) return <div style={cardStyle}>Loading market data...</div>;
  if (!dataA || !dataB) return <div style={cardStyle}>Failed to load data.</div>;

  const avgA = dataA.data.reduce((s, d) => s + d.lmp, 0) / dataA.data.length;
  const avgB = dataB.data.reduce((s, d) => s + d.lmp, 0) / dataB.data.length;

  const combined = dataA.data.map((d, i) => ({
    date: d.date.slice(0, 10),
    [isoA]: d.lmp,
    [isoB]: dataB.data[i]?.lmp ?? null,
  }));

  return (
    <div>
      <div style={metricStyle}>
        <div style={metricCard}>
          <div style={{ color: '#888', fontSize: 12 }}>{isoA} Avg Price</div>
          <div style={{ fontSize: 24, fontWeight: 700, color: '#00d4ff' }}>
            ${avgA.toFixed(2)}
          </div>
        </div>
        <div style={metricCard}>
          <div style={{ color: '#888', fontSize: 12 }}>{isoB} Avg Price</div>
          <div style={{ fontSize: 24, fontWeight: 700, color: '#ff6b6b' }}>
            ${avgB.toFixed(2)}
          </div>
        </div>
        <div style={metricCard}>
          <div style={{ color: '#888', fontSize: 12 }}>Avg Spread</div>
          <div style={{ fontSize: 24, fontWeight: 700, color: '#51cf66' }}>
            ${(avgA - avgB).toFixed(2)}
          </div>
        </div>
      </div>

      <div style={cardStyle}>
        <h3 style={{ marginTop: 0 }}>Daily Average LMP</h3>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={combined}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="date" stroke="#888" tick={{ fontSize: 11 }} />
            <YAxis stroke="#888" />
            <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid #333' }} />
            <Legend />
            <Line type="monotone" dataKey={isoA} stroke="#00d4ff" dot={false} strokeWidth={2} />
            <Line type="monotone" dataKey={isoB} stroke="#ff6b6b" dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
