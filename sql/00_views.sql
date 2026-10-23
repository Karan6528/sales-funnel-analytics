-- ============================================================================
-- 00_views.sql
-- Reusable views. Run automatically by src/load_to_sqlite.py.
-- ============================================================================

-- Cohort maturity
-- ---------------
-- A lead created last week has not had time to sign yet. Including it would
-- make conversion rates look worse than they are. For conversion analysis we
-- therefore only use leads that are at least ~8 weeks old, i.e. created before
-- the cut-off below. (The data ends on 2026-09-27.)
DROP VIEW IF EXISTS v_mature_leads;
CREATE VIEW v_mature_leads AS
SELECT *
FROM leads
WHERE created_at < '2026-08-01';

-- One row per lead with 0/1 flags for each funnel stage. Makes funnel maths a
-- simple SUM / AVG and keeps the other queries short.
DROP VIEW IF EXISTS v_funnel_flags;
CREATE VIEW v_funnel_flags AS
SELECT
    l.lead_id,
    l.created_at,
    l.lead_week,
    l.lead_month,
    l.channel,
    l.region,
    l.team,
    l.rep_id,
    l.product_interest,
    l.financing_type,
    l.speed_to_lead_bucket,
    l.offer_speed_bucket,
    l.hours_to_contact,
    l.days_appt_to_offer,
    l.contract_value_eur,
    1                                                     AS is_lead,
    CASE WHEN l.first_contact_at   IS NOT NULL THEN 1 ELSE 0 END AS is_contacted,
    CASE WHEN l.appointment_at     IS NOT NULL THEN 1 ELSE 0 END AS is_appointment,
    CASE WHEN l.offer_sent_at      IS NOT NULL THEN 1 ELSE 0 END AS is_offer,
    CASE WHEN l.contract_signed_at IS NOT NULL THEN 1 ELSE 0 END AS is_signed,
    CASE WHEN l.installed_at       IS NOT NULL THEN 1 ELSE 0 END AS is_installed,
    CASE WHEN l.cancelled_at       IS NOT NULL THEN 1 ELSE 0 END AS is_cancelled
FROM v_mature_leads AS l;
