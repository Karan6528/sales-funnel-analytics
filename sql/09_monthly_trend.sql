-- ============================================================================
-- 09_monthly_trend.sql
-- Question: How do lead volume and conversion develop over time (seasonality)?
-- Uses all leads by creation month. Conversion for the most recent months is
-- still incomplete (leads need time to sign), so it is flagged.
-- ============================================================================

SELECT
    lead_month,
    COUNT(*)                                                    AS leads,
    SUM(CASE WHEN contract_signed_at IS NOT NULL THEN 1 ELSE 0 END) AS signed,
    ROUND(100.0 * SUM(CASE WHEN contract_signed_at IS NOT NULL THEN 1 ELSE 0 END)
                / COUNT(*), 1)                                  AS lead_to_signed_pct,
    CASE WHEN lead_month >= '2026-08' THEN 'immature' ELSE 'mature' END AS cohort_status
FROM leads
GROUP BY lead_month
ORDER BY lead_month;
