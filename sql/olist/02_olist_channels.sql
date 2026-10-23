-- ============================================================================
-- 02_olist_channels.sql   (REAL data)
-- Question: Which marketing channels (origin) bring leads that become deals?
-- conversion_vs_avg_pp = percentage points above/below the overall rate.
-- ============================================================================

WITH by_channel AS (
    SELECT
        origin,
        COUNT(*)                         AS mqls,
        SUM(is_won)                      AS deals,
        AVG(is_won)                      AS conv,
        AVG(CASE WHEN is_won = 1 THEN days_to_close END) AS avg_days_to_close
    FROM v_olist_leads
    WHERE in_window = 1
    GROUP BY origin
),
overall AS (
    SELECT AVG(is_won) AS conv FROM v_olist_leads WHERE in_window = 1
)
SELECT
    c.origin,
    c.mqls,
    ROUND(100.0 * c.mqls / SUM(c.mqls) OVER (), 1)  AS share_of_mqls_pct,
    c.deals,
    ROUND(100.0 * c.conv, 1)                        AS conversion_pct,
    ROUND(100.0 * (c.conv - o.conv), 1)             AS conversion_vs_avg_pp,
    ROUND(c.avg_days_to_close, 1)                   AS avg_days_to_close
FROM by_channel AS c
CROSS JOIN overall AS o
ORDER BY c.mqls DESC;
