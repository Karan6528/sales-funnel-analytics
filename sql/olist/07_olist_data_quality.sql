-- ============================================================================
-- 07_olist_data_quality.sql   (REAL data)
-- Question: What can and can't we trust in this data?
-- Real CRM data is never clean; these checks shape what we conclude.
-- ============================================================================

SELECT 'Leads (MQLs) in file' AS check_name,
       COUNT(*)               AS value,
       'Jun 2017 - May 2018'  AS comment
FROM olist_mql
UNION ALL
SELECT 'Deals in file', COUNT(*), 'Won Dec 2017 - Nov 2018: earlier deals missing'
FROM olist_deals
UNION ALL
SELECT 'Deals without a matching lead', COUNT(*), 'Join integrity check'
FROM olist_deals WHERE mql_id NOT IN (SELECT mql_id FROM olist_mql)
UNION ALL
SELECT 'Leads with origin "unknown" or missing', COUNT(*),
       'Tracking gap: ~14% of leads, and they convert best'
FROM olist_mql WHERE origin IN ('unknown', '(missing)')
UNION ALL
SELECT 'Deals won before first contact', COUNT(*), 'Impossible date - excluded from timing'
FROM v_olist_leads WHERE days_to_close < 0
UNION ALL
SELECT 'Deals with declared monthly revenue = 0', COUNT(*),
       'Revenue field mostly empty - not used for value analysis'
FROM olist_deals WHERE declared_monthly_revenue = 0 OR declared_monthly_revenue IS NULL
UNION ALL
SELECT 'Deals missing has_company', COUNT(*), 'Field ~92% empty - not used'
FROM olist_deals WHERE has_company IS NULL;
