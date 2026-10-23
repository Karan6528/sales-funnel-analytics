-- ============================================================================
-- 01_funnel_overview.sql
-- Question: How many leads reach each stage, and where do we lose the most?
-- Output: one row per stage with volume, step conversion and overall conversion
-- ============================================================================

WITH totals AS (
    SELECT
        SUM(is_lead)        AS leads,
        SUM(is_contacted)   AS contacted,
        SUM(is_appointment) AS appointments,
        SUM(is_offer)       AS offers,
        SUM(is_signed)      AS signed,
        SUM(is_installed)   AS installed
    FROM v_funnel_flags
),
stages AS (
    SELECT 1 AS stage_order, 'Lead'        AS stage, leads        AS volume, leads        AS prev FROM totals UNION ALL
    SELECT 2, 'Contacted',   contacted,    leads        FROM totals UNION ALL
    SELECT 3, 'Appointment', appointments, contacted    FROM totals UNION ALL
    SELECT 4, 'Offer',       offers,       appointments FROM totals UNION ALL
    SELECT 5, 'Signed',      signed,       offers       FROM totals UNION ALL
    SELECT 6, 'Installed',   installed,    signed       FROM totals
)
SELECT
    stage_order,
    stage,
    volume,
    ROUND(100.0 * volume / prev, 1)                                AS step_conversion_pct,
    ROUND(100.0 * volume / (SELECT leads FROM totals), 1)          AS overall_conversion_pct,
    prev - volume                                                  AS lost_at_this_step
FROM stages
ORDER BY stage_order;
