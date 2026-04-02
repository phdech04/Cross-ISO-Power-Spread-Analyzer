-- Correlate weather to price with lagged features
SELECT
    p.timestamp,
    p.iso,
    p.lmp,
    w.temp_c,
    w.wind_speed,
    w.solar_radiation,
    w.cdd,
    w.hdd,
    LAG(p.lmp, 1) OVER (
        PARTITION BY p.iso ORDER BY p.timestamp
    ) AS lmp_1h_ago,
    LAG(p.lmp, 24) OVER (
        PARTITION BY p.iso ORDER BY p.timestamp
    ) AS lmp_24h_ago,
    p.lmp - LAG(p.lmp, 24) OVER (
        PARTITION BY p.iso ORDER BY p.timestamp
    ) AS price_change_24h,
    AVG(p.lmp) OVER (
        PARTITION BY p.iso
        ORDER BY p.timestamp
        ROWS BETWEEN 23 PRECEDING AND CURRENT ROW
    ) AS lmp_24h_rolling_avg
FROM hourly_prices p
JOIN hourly_weather w
    ON p.timestamp = w.timestamp
    AND p.iso = w.iso
ORDER BY p.iso, p.timestamp;
