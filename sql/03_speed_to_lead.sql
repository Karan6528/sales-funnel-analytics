-- ============================================================================
-- 03_speed_to_lead.sql
-- Question: Does it matter how fast the sales team calls a new lead?
-- Approach: bucket contacted leads by hours until first contact and compare
--           appointment and signing rates.
-- ============================================================================

SELECT
    speed_to_lead_bucket,
    COUNT(*)                                          AS contacted_leads,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share_of_leads_pct,
    ROUND(100.0 * AVG(is_appointment), 1)             AS appointment_rate_pct,
    ROUND(100.0 * AVG(is_signed), 1)                  AS signed_rate_pct
FROM v_funnel_flags
WHERE is_contacted = 1
GROUP BY speed_to_lead_bucket
ORDER BY CASE speed_to_lead_bucket
            WHEN 'Under 1h'     THEN 1
            WHEN '1-4h'     THEN 2
            WHEN '4-24h'    THEN 3
            WHEN '1-3 days' THEN 4
            ELSE 5
         END;
