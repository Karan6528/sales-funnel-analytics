-- ============================================================================
-- 01_olist_monthly.sql   (REAL data)
-- Question: How do lead volume and lead -> deal conversion develop by month?
-- Shows why 2017 must be excluded: deals before Dec 2017 are missing from the
-- extract, so 2017 conversion is artificially near zero.
-- ============================================================================

SELECT
    lead_month,
    COUNT(*)                                  AS mqls,
    SUM(is_won)                               AS deals,
    ROUND(100.0 * AVG(is_won), 1)             AS conversion_pct,
    CASE WHEN MAX(in_window) = 1 THEN 'in window'
         ELSE 'excluded (deal data incomplete)' END AS note
FROM v_olist_leads
GROUP BY lead_month
ORDER BY lead_month;
