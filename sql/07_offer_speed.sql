-- ============================================================================
-- 07_offer_speed.sql
-- Question: Do customers sign less often when the offer takes long to arrive?
-- ============================================================================

SELECT
    offer_speed_bucket,
    COUNT(*)                                   AS offers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share_of_offers_pct,
    SUM(is_signed)                             AS signed,
    ROUND(100.0 * AVG(is_signed), 1)           AS offer_to_signed_pct
FROM v_funnel_flags
WHERE is_offer = 1
GROUP BY offer_speed_bucket
ORDER BY CASE offer_speed_bucket
            WHEN 'Up to 3 days' THEN 1
            WHEN '4-7 days'  THEN 2
            ELSE 3
         END;
