-- Fato pedidos: um registro por pedido.
SELECT
    o.order_id,
    o.customer_id,
    o.order_purchase_timestamp::date AS data_compra,
    o.order_status,
    o.order_status NOT IN ('canceled', 'unavailable') AS pedido_valido,
    o.order_delivered_customer_date IS NOT NULL AS entregue,
    o.order_delivered_customer_date IS NOT NULL
        AND o.order_delivered_customer_date > o.order_estimated_delivery_date AS atrasado,
    CASE WHEN o.order_delivered_customer_date IS NOT NULL
         THEN o.order_delivered_customer_date::date - o.order_purchase_timestamp::date
    END AS prazo_entrega_dias
FROM olist.orders o
