-- ============================================================================
-- 04_team_performance.sql
-- Question: Do the regional sales teams perform differently, and at which
--           stage of the funnel?
-- ============================================================================

SELECT
    team,
    COUNT(*)                                                         AS leads,
    -- Speed: share of leads called within 4 hours
    ROUND(100.0 * SUM(CASE WHEN hours_to_contact < 4 THEN 1 ELSE 0 END)
                / SUM(is_contacted), 1)                              AS contacted_within_4h_pct,
    ROUND(AVG(hours_to_contact), 1)                                  AS avg_hours_to_contact,
    -- Conversion by stage
    ROUND(100.0 * SUM(is_appointment) / SUM(is_contacted), 1)        AS contact_to_appt_pct,
    ROUND(100.0 * SUM(is_offer) / SUM(is_appointment), 1)            AS appt_to_offer_pct,
    ROUND(AVG(days_appt_to_offer), 1)                                AS avg_days_appt_to_offer,
    ROUND(100.0 * SUM(CASE WHEN days_appt_to_offer > 7 THEN 1 ELSE 0 END)
                / SUM(is_offer), 1)                                  AS offers_over_7_days_pct,
    ROUND(100.0 * SUM(is_signed) / SUM(is_offer), 1)                 AS offer_to_signed_pct,
    SUM(is_signed)                                                   AS signed,
    ROUND(100.0 * SUM(is_signed) / COUNT(*), 1)                      AS lead_to_signed_pct
FROM v_funnel_flags
GROUP BY team
ORDER BY lead_to_signed_pct DESC;
