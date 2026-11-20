"""Auditable order-level review playbooks. Only aggregates leave the database."""

from .data import rows
from .plans import iso_day


SPECS = {
    'reviews-aftercare': {
        'title': 'Reviews and aftercare',
        'description': 'Find products with the most low ratings and see which issues customers mention.',
        'scope': 'Delivered, single-product orders with a valid rating. Portuguese text rules cover quality, delivery, listing accuracy and service.',
        'question': 'Which products receive the most low ratings, and what do their customers mention?',
        'steps': ['Select one valid review per attributable order.', 'Separate star ratings from written sentiment.', 'Prioritize products by low-rating workload and inspect recurring themes.'],
    },
    'merchant-score': {
        'title': 'Merchant scorecard',
        'description': 'Rank sellers by customer ratings and on-time delivery, with the sample behind each score.',
        'scope': 'Delivered, single-seller orders. Sellers need at least 20 ratings and 20 timed deliveries. Comment sentiment is reported separately.',
        'question': 'How do merchants rank on customer ratings and on-time delivery?',
        'steps': ['Attribute each delivered order to one seller.', 'Adjust ratings and punctuality for sample size.', 'Rank eligible sellers and inspect feedback coverage.'],
    },
}

# Phrase-level exceptions handle common Portuguese negations before individual words.
# The SQL returned to the reader contains the exact lexicon used for this run.
_TEXT = r"""
, phrases AS (
    SELECT *,
        regexp_replace(words, '\b(bom dia|boa tarde|boa noite)\b', ' ', 'g') AS feedback,
        regexp_replace(feedback, '\b(sem (nenhum |nenhuma )?(problemas?|defeitos?)|nao (tive|houve) (nenhum |nenhuma )?problemas?|nao (veio|chegou) (quebrad[oa]|danificad[oa])|nao atrasou|nao (e |foi |era )?ruim)\b', ' sinalpositivo ', 'g') AS reassuring,
        regexp_replace(reassuring, '\b(nao (e |foi |era |muito )?(gostei|gostamos|recomendo|recomendaria|bom|boa|otim[oa]|satisf[ei]it[oa]|recebi|chegou|funciona|funcionou|entregaram)|nao (foi |foi bem )?entregue|sem qualidade)\b', ' sinalnegativo ', 'g') AS polarity_words
    FROM attributed
), labeled AS (
    SELECT *,
        regexp_matches(polarity_words, '\b(sinalpositivo|excelentes?|otim[oa]s?|perfeit[oa]s?|adorei|gostei|gostamos|recomendo|satisfeit[oa]s?|maravilhos[oa]s?|bem embalad[oa]|antes do prazo|bom|bons|boas?)\b') AS positive,
        regexp_matches(polarity_words, '\b(sinalnegativo|pessim[oa]s?|ruim|ruins|horrivel|horriveis|decepcion\w*|insatisfeit\w*|defeit\w*|quebrad[oa]s?|danificad[oa]s?|atras\w*|demor\w*|avariad[oa]s?|arrepend\w*)\b') AS negative
    FROM phrases
), signals AS (
    SELECT *, CASE WHEN NOT has_text THEN NULL
        WHEN positive AND negative THEN 'mixed'
        WHEN positive THEN 'positive' WHEN negative THEN 'negative'
        ELSE 'unclassified' END AS sentiment
    FROM labeled
)
"""

_SENTIMENT_COUNTS = """
    count(*) FILTER (WHERE has_text) AS written_comments,
    round(100.0 * written_comments / nullif(rated_orders, 0), 1) AS text_coverage_pct,
    count(*) FILTER (WHERE sentiment = 'positive') AS positive_text,
    count(*) FILTER (WHERE sentiment = 'negative') AS negative_text,
    count(*) FILTER (WHERE sentiment = 'mixed') AS mixed_text,
    count(*) FILTER (WHERE sentiment = 'unclassified') AS unclassified_text
"""

_MERCHANT = f"""
, seller_counts AS (
    SELECT seller_id, count(*) AS delivered_orders, count(review_score) AS rated_orders,
        count(on_time) AS timed_orders, sum((review_score - 1) / 4.0) AS rating_points,
        sum(on_time::INT) AS on_time_orders,
        {_SENTIMENT_COUNTS}
    FROM signals GROUP BY seller_id
), market AS (
    SELECT sum(rating_points) / nullif(sum(rated_orders), 0) AS rating_prior,
           sum(on_time_orders) / nullif(sum(timed_orders), 0) AS delivery_prior
    FROM seller_counts
), eligible AS (
    SELECT *, 100 * (rating_points + 20 * rating_prior) / (rated_orders + 20) AS quality,
        100 * (on_time_orders + 20 * delivery_prior) / (timed_orders + 20) AS punctuality
    FROM seller_counts CROSS JOIN market
    WHERE rated_orders >= 20 AND timed_orders >= 20
), scored AS (
    SELECT *, round(0.70 * quality + 0.30 * punctuality, 2) AS score FROM eligible
)
SELECT rank() OVER (ORDER BY score DESC) AS rank, seller_id, score,
    round(quality, 2) AS rating_component, round(punctuality, 2) AS delivery_component,
    rated_orders, timed_orders, delivered_orders, round(1 + 4 * rating_points / rated_orders, 3) AS mean_stars,
    on_time_orders, written_comments, text_coverage_pct, positive_text, negative_text, mixed_text, unclassified_text,
    round(rating_prior * 100, 4) AS market_rating_points, round(delivery_prior * 100, 4) AS market_delivery_points,
    count(*) OVER () AS eligible_sellers
FROM scored ORDER BY score DESC, seller_id
"""

_THEMES = {
    'delivery': r'\b(entrega\w*|atras\w*|demor\w*|prazo\w*|transportadora\w*|correios|frete)\b',
    'quality': r'\b(qualidade|defeit\w*|quebrad\w*|danificad\w*|avariad\w*|fragil|estragad\w*|nao funciona\w*)\b',
    'listing': r'\b(descricao|anuncio|anunciad\w*|foto\w*|diferente|errad[oa]s?)\b',
    'service': r'\b(atendimento|suporte|atendente\w*|contato|sac|resposta|responde\w*)\b',
}
_THEME_COUNTS = ',\n        '.join(
    f"count(*) FILTER (WHERE review_score <= 2 AND regexp_matches(words, '{pattern}')) AS {theme}_mentions"
    for theme, pattern in _THEMES.items()
)

_PRODUCT = f"""
, product_counts AS (
    SELECT product_id, grouping(product_id) AS overall, count(*) AS rated_orders,
        count(*) FILTER (WHERE review_score <= 2) AS low_ratings,
        round(100.0 * low_ratings / rated_orders, 1) AS low_rating_pct,
        {_SENTIMENT_COUNTS},
        {_THEME_COUNTS}
    FROM signals WHERE review_score IS NOT NULL
    GROUP BY GROUPING SETS ((), (product_id)) HAVING count(*) > 0
)
SELECT CASE WHEN overall = 1 THEN 'All attributable products' ELSE 'Product' END AS scope, pc.product_id,
    CASE WHEN overall = 0 THEN coalesce(t.product_category_name_english, p.product_category_name, 'unknown') END AS category,
    pc.* EXCLUDE (overall, product_id)
FROM product_counts pc LEFT JOIN products p ON pc.product_id = p.product_id
LEFT JOIN category_translation t ON t.product_category_name = p.product_category_name
ORDER BY overall DESC, low_ratings DESC, rated_orders DESC, pc.product_id LIMIT 21
"""


def _order_sample(skill_id, start, end):
    entity, dimension = ('seller_id', 'sellers') if skill_id == 'merchant-score' else ('product_id', 'products')
    conditions = ["o.order_status = 'delivered'"]
    if start:
        conditions.append(f"o.order_purchase_timestamp >= DATE '{iso_day(start)}'")
    if end:
        conditions.append(f"o.order_purchase_timestamp < DATE '{iso_day(end)}'")
    return f"""
WITH ownership AS (
    SELECT order_id, min({entity}) AS {entity} FROM order_items GROUP BY order_id
    HAVING count(DISTINCT {entity}) = 1 AND count({entity}) = count(*)
), latest AS (
    SELECT order_id, review_score,
        trim(concat_ws(' ', review_comment_title, review_comment_message)) AS body
    FROM order_reviews WHERE review_score BETWEEN 1 AND 5
    QUALIFY row_number() OVER (PARTITION BY order_id ORDER BY review_answer_timestamp DESC NULLS LAST,
        review_creation_date DESC NULLS LAST, review_id ASC NULLS LAST, source_row ASC) = 1
), attributed AS (
    SELECT a.{entity}, r.review_score, coalesce(length(trim(regexp_replace(r.body, '\\s+', ' ', 'g'))) > 0, false) AS has_text,
        trim(regexp_replace(strip_accents(lower(coalesce(r.body, ''))), '[^a-z]+', ' ', 'g')) AS words,
        o.order_delivered_customer_date::DATE <= o.order_estimated_delivery_date::DATE AS on_time
    FROM orders o JOIN ownership a USING (order_id) JOIN {dimension} d USING ({entity})
    LEFT JOIN latest r USING (order_id) WHERE {' AND '.join(conditions)}
)
"""


def run(con, skill_id, start=None, end=None):
    if skill_id not in SPECS:
        raise ValueError('unknown_review_skill')
    merchant = skill_id == 'merchant-score'
    sql = (_order_sample(skill_id, start, end) + _TEXT + (_MERCHANT if merchant else _PRODUCT)).strip()
    table = rows(con, sql)
    warnings = [
        'Ratings cover whole orders. Attribution requires one known seller per order.' if merchant else
        'Product rows require one known product per order. Multiple units of that product count once.',
        'Portuguese phrase matching can miss negation, sarcasm and unfamiliar terms. Missing comments carry no text label.',
    ]
    if merchant:
        warnings.append('The score combines customer and carrier experience. Comment sentiment is reported separately. Equal scores share rank.')
        if table:
            top = table[0]
            placing = 'shares first place' if len(table) > 1 and table[1]['rank'] == 1 else 'ranks first'
            answer = (f"Seller {top['seller_id']} {placing} at {top['score']:.2f}/100 among {top['eligible_sellers']:,} eligible sellers. "
                      f"It has {top['rated_orders']:,} rated orders and {top['on_time_orders']:,} on-time arrivals in {top['timed_orders']:,} timed deliveries. "
                      'Inspect both adjusted components before selecting a seller for operational follow-up.')
        else:
            answer = 'No seller has both 20 valid ratings and 20 timed deliveries in this purchase window.'
    else:
        warnings.append('Theme counts describe mentions in 1–2 star reviews. One comment can mention several topics. Return and refund events are unavailable.')
        if table:
            total, product = table[:2]
            answer = (f"{total['low_ratings']:,} of {total['rated_orders']:,} attributable rated orders received 1–2 stars "
                      f"({total['low_rating_pct']:.1f}%). Of {total['written_comments']:,} written reviews, "
                      f"{total['positive_text']:,} matched positive language only and {total['negative_text']:,} matched negative language only. "
                      f"Product {product['product_id']} has {product['low_ratings']:,} low ratings across {product['rated_orders']:,} rated orders. ")
            if total['low_ratings']:
                theme = max(_THEMES, key=lambda key: total[key + '_mentions'])
                mentions = total[theme + '_mentions']
                if mentions:
                    answer += f"{theme.capitalize()} appears in {mentions:,} low ratings, the highest count among the four tracked themes. Start the review there."
                else:
                    answer += 'The low ratings have no recognized theme. Inspect additional feedback before choosing a remedy.'
            else:
                answer += 'There are no low-rating cases in this sample.'
        else:
            answer = 'No delivered single-product order has a valid rating in this purchase window.'
    return dict(answer=answer, table=table, sql=sql, warnings=warnings)
