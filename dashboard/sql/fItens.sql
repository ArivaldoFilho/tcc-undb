-- Fato itens: um registro por item de pedido.
SELECT
    oi.order_id,
    oi.order_item_id,
    oi.product_id,
    oi.seller_id,
    o.customer_id,
    o.order_purchase_timestamp::date AS data_compra,
    o.order_status NOT IN ('canceled', 'unavailable') AS pedido_valido,
    oi.price,
    oi.freight_value
FROM olist.order_items oi
JOIN olist.orders o ON o.order_id = oi.order_id
