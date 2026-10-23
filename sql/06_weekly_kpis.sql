-- ============================================================================
-- 06_weekly_kpis.sql
-- Question: What happened in each of the last 12 weeks? (management report)
-- Unlike the cohort queries, this counts EVENTS in the week they happened:
-- leads created, appointments held, offers sent and contracts signed that week.
-- Week-over-week change uses the LAG window function.
-- ============================================================================

WITH weeks AS (
    SELECT DISTINCT lead_week AS week_start
    FROM leads
    WHERE lead_week >= DATE((SELECT MAX(lead_week) FROM leads), '-77 days')  -- last 12 weeks
),
events AS (
    SELECT DATE(created_at, 'weekday 0', '-6 days')         AS week_start, 'lead'  AS event, 0 AS value FROM leads
    UNION ALL
    SELECT DATE(appointment_at, 'weekday 0', '-6 days'), 'appointment', 0 FROM leads WHERE appointment_at IS NOT NULL
    UNION ALL
    SELECT DATE(offer_sent_at, 'weekday 0', '-6 days'), 'offer', 0 FROM leads WHERE offer_sent_at IS NOT NULL
    UNION ALL
    SELECT DATE(contract_signed_at, 'weekday 0', '-6 days'), 'signed', contract_value_eur
    FROM leads WHERE contract_signed_at IS NOT NULL
),
weekly AS (
    SELECT
        w.week_start,
        SUM(CASE WHEN e.event = 'lead'        THEN 1 ELSE 0 END) AS new_leads,
        SUM(CASE WHEN e.event = 'appointment' THEN 1 ELSE 0 END) AS appointments,
        SUM(CASE WHEN e.event = 'offer'       THEN 1 ELSE 0 END) AS offers_sent,
        SUM(CASE WHEN e.event = 'signed'      THEN 1 ELSE 0 END) AS contracts_signed,
        SUM(CASE WHEN e.event = 'signed'      THEN e.value ELSE 0 END) AS signed_value_eur
    FROM weeks AS w
    LEFT JOIN events AS e ON e.week_start = w.week_start
    GROUP BY w.week_start
)
SELECT
    week_start,
    new_leads,
    appointments,
    offers_sent,
    contracts_signed,
    ROUND(signed_value_eur, 0)                                              AS signed_value_eur,
    ROUND(100.0 * (contracts_signed - LAG(contracts_signed) OVER w)
                / LAG(contracts_signed) OVER w, 1)                          AS signed_wow_pct,
    ROUND(AVG(contracts_signed) OVER (w ROWS BETWEEN 3 PRECEDING AND CURRENT ROW), 1)
                                                                            AS signed_4wk_avg
FROM weekly
WINDOW w AS (ORDER BY week_start)
ORDER BY week_start;
