import axios from 'axios';

const API_BASE = '/api';

export async function fetchISOs() {
  const res = await axios.get(`${API_BASE}/isos`);
  return res.data.isos;
}

export async function fetchPrices(iso, days = 365) {
  const res = await axios.get(`${API_BASE}/prices`, { params: { iso, days } });
  return res.data;
}

export async function fetchSpread(isoA, isoB, days = 365) {
  const res = await axios.get(`${API_BASE}/spread`, {
    params: { iso_a: isoA, iso_b: isoB, days },
  });
  return res.data;
}

export async function runBacktest(params) {
  const res = await axios.get(`${API_BASE}/backtest`, { params });
  return res.data;
}

export async function fetchRisk(isoA, isoB, days = 365) {
  const res = await axios.get(`${API_BASE}/risk`, {
    params: { iso_a: isoA, iso_b: isoB, days },
  });
  return res.data;
}
