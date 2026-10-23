-- ============================================================================
-- 00_olist_views.sql   (REAL data: Olist marketing funnel, Kaggle)
-- One row per marketing qualified lead (MQL), joined to the closed deal if any.
--
-- Analysis window
-- ---------------
-- The closed-deals table only contains deals won from Dec 2017 onwards, while
-- leads go back to Jun 2017. Leads from 2017 therefore look like they almost
-- never convert - an artefact of the data extract, not of sales performance.
-- Conversion analysis uses leads from 2018-01-01 onwards (in_window = 1).
-- ============================================================================

DROP VIEW IF EXISTS v_olist_leads;
CREATE VIEW v_olist_leads AS
SELECT
    m.mql_id,
    m.first_contact_date,
    SUBSTR(m.first_contact_date, 1, 7)                       AS lead_month,
    m.landing_page_id,
    m.origin,
    d.won_date,
    d.sdr_id,                                   -- sales development rep (qualifies)
    d.sr_id,                                    -- sales rep (closes)
    d.business_segment,
    d.lead_type,
    d.lead_behaviour_profile,
    d.business_type,
    CASE WHEN d.mql_id IS NOT NULL THEN 1 ELSE 0 END          AS is_won,
    CAST(JULIANDAY(DATE(d.won_date)) - JULIANDAY(m.first_contact_date) AS INTEGER)
                                                             AS days_to_close,
    CASE WHEN m.first_contact_date >= '2018-01-01' THEN 1 ELSE 0 END AS in_window
FROM olist_mql        AS m
LEFT JOIN olist_deals AS d USING (mql_id);
