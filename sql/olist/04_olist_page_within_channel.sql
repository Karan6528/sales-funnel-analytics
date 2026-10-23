-- ============================================================================
-- 04_olist_page_within_channel.sql   (REAL data)
-- Question: Are the two best landing pages better only because they get
--           better traffic? Compare them with other pages WITHIN each channel.
-- If the top pages also win inside the same channel, the page itself (form,
-- offer, message) is the likely driver - worth an A/B test.
-- ============================================================================

WITH top_pages AS (
    SELECT landing_page_id
    FROM v_olist_leads
    WHERE in_window = 1
    GROUP BY landing_page_id
    ORDER BY COUNT(*) DESC
    LIMIT 2
),
flagged AS (
    SELECT
        l.origin,
        l.is_won,
        CASE WHEN t.landing_page_id IS NOT NULL THEN 1 ELSE 0 END AS is_top_page
    FROM v_olist_leads AS l
    LEFT JOIN top_pages AS t USING (landing_page_id)
    WHERE l.in_window = 1
)
SELECT
    origin,
    SUM(is_top_page)                                                       AS mqls_top_pages,
    ROUND(100.0 * SUM(is_won * is_top_page) / NULLIF(SUM(is_top_page), 0), 1)
                                                                           AS conv_top_pages_pct,
    SUM(1 - is_top_page)                                                   AS mqls_other_pages,
    ROUND(100.0 * SUM(is_won * (1 - is_top_page)) / NULLIF(SUM(1 - is_top_page), 0), 1)
                                                                           AS conv_other_pages_pct
FROM flagged
GROUP BY origin
HAVING SUM(is_top_page) >= 50          -- only channels with enough top-page traffic
ORDER BY mqls_top_pages DESC;
