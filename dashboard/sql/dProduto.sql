-- Produtos sem categoria ficam como "(sem categoria)"; categorias sem tradução
-- mantêm o nome em português na coluna em inglês.
SELECT
    p.product_id,
    COALESCE(p.product_category_name, '(sem categoria)') AS categoria,
    COALESCE(t.product_category_name_english, p.product_category_name, '(no category)') AS categoria_en
FROM olist.products p
LEFT JOIN olist.product_category_name_translation t
       ON t.product_category_name = p.product_category_name
