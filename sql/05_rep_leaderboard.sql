-- ============================================================================
-- 05_rep_leaderboard.sql
-- Question: Which sales reps close best once an offer is out?
-- Note: only reps with at least 50 offers are ranked, so small samples don't
--       produce misleading winners. Offer->signed is used because reps don't
--       choose which leads they receive, but they do control the closing.
-- ============================================================================

WITH rep_stats AS (
    SELECT
        f.rep_id,
        r.rep_name,
        r.team,
        COUNT(*)                                           AS leads,
        SUM(f.is_offer)                                    AS offers,
        SUM(f.is_signed)                                   AS signed,
        ROUND(100.0 * SUM(f.is_signed) / SUM(f.is_offer), 1) AS offer_to_signed_pct,
        ROUND(SUM(CASE WHEN f.is_signed = 1 THEN f.contract_value_eur ELSE 0 END), 0)
                                                           AS signed_value_eur
    FROM v_funnel_flags AS f
    JOIN sales_reps     AS r USING (rep_id)
    GROUP BY f.rep_id, r.rep_name, r.team
    HAVING SUM(f.is_offer) >= 50
)
SELECT
    RANK() OVER (ORDER BY offer_to_signed_pct DESC)          AS rank,
    rep_id,
    rep_name,
    team,
    leads,
    offers,
    signed,
    offer_to_signed_pct,
    ROUND(offer_to_signed_pct
          - AVG(offer_to_signed_pct) OVER (PARTITION BY team), 1) AS vs_team_avg_pp,
    signed_value_eur
FROM rep_stats
ORDER BY rank;
