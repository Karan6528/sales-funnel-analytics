-- ============================================================================
-- 02_channel_performance.sql
-- Question: Which marketing channels bring leads that actually sign, and what
--           does a signed contract cost per channel?
-- Key metrics:
--   lead_to_signed_pct  share of leads that sign
--   cost_per_lead       spend / leads
--   cost_per_signed     spend / signed contracts  (customer acquisition cost)
--   revenue_per_eur     signed contract value per EUR of marketing spend
-- ============================================================================

WITH funnel AS (
    SELECT
        channel,
        COUNT(*)                                   AS leads,
        SUM(is_appointment)                        AS appointments,
        SUM(is_offer)                              AS offers,
        SUM(is_signed)                             AS signed,
        SUM(CASE WHEN is_signed = 1 THEN contract_value_eur ELSE 0 END) AS signed_value_eur
    FROM v_funnel_flags
    GROUP BY channel
),
spend AS (
    SELECT channel, SUM(spend_eur) AS spend_eur
    FROM marketing_spend
    WHERE week_start < '2026-08-01'          -- same period as the mature cohort
    GROUP BY channel
)
SELECT
    f.channel,
    f.leads,
    ROUND(100.0 * f.appointments / f.leads, 1)            AS lead_to_appt_pct,
    ROUND(100.0 * f.signed / f.appointments, 1)           AS appt_to_signed_pct,
    f.signed,
    ROUND(100.0 * f.signed / f.leads, 1)                  AS lead_to_signed_pct,
    ROUND(s.spend_eur, 0)                                 AS spend_eur,
    ROUND(s.spend_eur / f.leads, 0)                       AS cost_per_lead,
    ROUND(s.spend_eur / NULLIF(f.signed, 0), 0)           AS cost_per_signed,
    ROUND(f.signed_value_eur, 0)                          AS signed_value_eur,
    ROUND(f.signed_value_eur / s.spend_eur, 1)            AS revenue_per_eur_spent
FROM funnel AS f
JOIN spend  AS s USING (channel)
ORDER BY cost_per_signed;
