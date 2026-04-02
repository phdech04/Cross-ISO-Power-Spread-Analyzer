-- Average hourly price shape by ISO and month
SELECT
    iso,
    EXTRACT(MONTH FROM timestamp) AS month,
    EXTRACT(HOUR FROM timestamp) AS hour,
    AVG(lmp) AS avg_price,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY lmp) AS p95_price,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY lmp) AS p05_price,
    STDDEV(lmp) AS hourly_vol,
    COUNT(*) AS obs_count
FROM hourly_prices
GROUP BY iso,
    EXTRACT(MONTH FROM timestamp),
    EXTRACT(HOUR FROM timestamp)
ORDER BY iso, month, hour;
