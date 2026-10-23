-- ============================================================================
-- 08_lost_reasons.sql
-- Question: Why do we lose deals, and at which stage?
-- The stage is the last stage the lead reached before being marked lost.
-- ============================================================================

SELECT
    CASE
        WHEN cancelled_at       IS NOT NULL THEN '5 After signing'
        WHEN offer_sent_at      IS NOT NULL THEN '4 After offer'
        WHEN appointment_at     IS NOT NULL THEN '3 After appointment'
        WHEN first_contact_at   IS NOT NULL THEN '2 After first contact'
        ELSE                                     '1 Before contact'
    END                                                      AS lost_stage,
    lost_reason,
    COUNT(*)                                                 AS leads_lost,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)       AS share_of_all_lost_pct
FROM v_mature_leads
WHERE lost_reason IS NOT NULL
GROUP BY lost_stage, lost_reason
ORDER BY lost_stage, leads_lost DESC;
