-- ============================================================================
-- 06_olist_closer_concentration.sql   (REAL data)
-- Question: How dependent is the business on a few sales reps (closers)?
-- Running share of deals from the top reps down (a Pareto view).
-- Note: the data only has the rep for WON deals, so this measures volume and
-- speed, not win rate.
-- ============================================================================

WITH reps AS (
    SELECT
        sr_id,
        COUNT(*)                     AS deals,
        ROUND(AVG(days_to_close), 1) AS avg_days_to_close
    FROM v_olist_leads
    WHERE in_window = 1 AND is_won = 1
    GROUP BY sr_id
)
SELECT
    ROW_NUMBER() OVER (ORDER BY deals DESC, sr_id)                  AS rank,
    'rep_' || SUBSTR(sr_id, 1, 6)                                   AS sales_rep,
    deals,
    ROUND(100.0 * deals / SUM(deals) OVER (), 1)                    AS share_pct,
    ROUND(100.0 * SUM(deals) OVER (ORDER BY deals DESC, sr_id
                                   ROWS UNBOUNDED PRECEDING)
                / SUM(deals) OVER (), 1)                            AS cumulative_share_pct,
    avg_days_to_close
FROM reps
ORDER BY rank;
