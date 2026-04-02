-- Compute daily average spread between two ISOs
-- Parameters: $1 = iso_a, $2 = iso_b
WITH daily AS (
    SELECT
        DATE_TRUNC('day', timestamp) AS trade_date,
        iso,
        AVG(lmp) AS avg_lmp,
        MAX(lmp) AS peak_lmp,
        MIN(lmp) AS offpeak_lmp,
        STDDEV(lmp) AS intraday_vol,
        AVG(CASE WHEN EXTRACT(HOUR FROM timestamp)
            BETWEEN 7 AND 22 THEN lmp END) AS onpeak_avg,
        AVG(CASE WHEN EXTRACT(HOUR FROM timestamp)
            NOT BETWEEN 7 AND 22 THEN lmp END) AS offpeak_avg
    FROM hourly_prices
    GROUP BY 1, 2
)
SELECT
    a.trade_date,
    a.avg_lmp AS iso_a_price,
    b.avg_lmp AS iso_b_price,
    a.avg_lmp - b.avg_lmp AS spread,
    a.onpeak_avg - b.onpeak_avg AS onpeak_spread,
    a.offpeak_avg - b.offpeak_avg AS offpeak_spread,
    a.intraday_vol AS vol_a,
    b.intraday_vol AS vol_b
FROM daily a
JOIN daily b ON a.trade_date = b.trade_date
WHERE a.iso = $1 AND b.iso = $2
ORDER BY a.trade_date;
