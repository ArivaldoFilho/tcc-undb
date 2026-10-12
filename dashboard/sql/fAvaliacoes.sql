-- Fato avaliações: um registro por avaliação (review_id, order_id).
SELECT
    r.review_id,
    r.order_id,
    o.customer_id,
    o.order_purchase_timestamp::date AS data_compra,
    r.review_score
FROM olist.order_reviews r
JOIN olist.orders o ON o.order_id = r.order_id
