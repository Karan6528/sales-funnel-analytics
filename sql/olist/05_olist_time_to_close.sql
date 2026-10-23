-- ============================================================================
-- 05_olist_time_to_close.sql   (REAL data)
-- Question: How long does it take to close a deal after first contact?
-- Days are counted from the first contact date to the won date.
-- ============================================================================

SELECT
    CASE
        WHEN days_to_close <= 7  THEN '1) 0-7 days'
        WHEN days_to_close <= 30 THEN '2) 8-30 days'
        WHEN days_to_close <= 90 THEN '3) 31-90 days'
        ELSE                          '4) over 90 days'
    END                                                     AS time_to_close,
    COUNT(*)                                                AS deals,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)      AS share_pct,
    ROUND(100.0 * SUM(COUNT(*)) OVER (ORDER BY MIN(days_to_close))
                / SUM(COUNT(*)) OVER (), 1)                 AS cumulative_pct
FROM v_olist_leads
WHERE in_window = 1
  AND is_won = 1
  AND days_to_close >= 0          -- excludes the 1 deal with an impossible date
GROUP BY time_to_close
ORDER BY time_to_close;
