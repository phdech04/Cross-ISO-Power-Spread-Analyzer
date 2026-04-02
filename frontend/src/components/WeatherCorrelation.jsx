import React from 'react';

const cardStyle = {
  background: '#1a1a2e',
  borderRadius: 8,
  padding: 20,
  marginBottom: 20,
};

export default function WeatherCorrelation({ isoA, isoB, days }) {
  return (
    <div>
      <div style={cardStyle}>
        <h3 style={{ marginTop: 0 }}>Weather-Price Correlation</h3>
        <p style={{ color: '#aaa' }}>
          Weather correlation analysis requires the backend weather endpoint.
          Start the FastAPI server and this panel will display:
        </p>
        <ul style={{ color: '#aaa' }}>
          <li>Temperature vs. Price scatter (V-shaped response)</li>
          <li>Wind speed impact on {isoA} and {isoB}</li>
          <li>Solar radiation impact (CAISO duck curve)</li>
          <li>Lagged weather signal correlation</li>
        </ul>
        <p style={{ color: '#666', fontSize: 13 }}>
          For full weather analysis, see the Streamlit dashboard or notebook 03.
        </p>
      </div>
    </div>
  );
}
