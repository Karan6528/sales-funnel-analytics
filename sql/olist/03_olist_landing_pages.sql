-- ============================================================================
-- 03_olist_landing_pages.sql   (REAL data)
-- Question: Do some landing pages (sign-up forms) produce much better leads?
-- Pages with at least 100 leads are shown individually; the long tail of
-- smaller pages is grouped as 'All other pages'.
-- ============================================================================

WITH pages AS (
    SELECT
        landing_page_id,
        COUNT(*)      AS mqls,
        SUM(is_won)   AS deals
    FROM v_olist_leads
    WHERE in_window = 1
    GROUP BY landing_page_id
),
labelled AS (
    SELECT
        CASE WHEN mqls >= 100 THEN 'page_' || SUBSTR(landing_page_id, 1, 6)
             ELSE 'All other pages' END                   AS landing_page,
        mqls,
        deals
    FROM pages
)
SELECT
    landing_page,
    SUM(mqls)                                            AS mqls,
    SUM(deals)                                           AS deals,
    ROUND(100.0 * SUM(deals) / SUM(mqls), 1)             AS conversion_pct,
    ROUND(100.0 * SUM(mqls) / SUM(SUM(mqls)) OVER (), 1) AS share_of_mqls_pct
FROM labelled
GROUP BY landing_page
ORDER BY landing_page = 'All other pages', mqls DESC;
