INSERT INTO target.catalog ('id', 'product_id', 'product_name', 'product_description', 'colors', 'price', 'cost')
SELECT p.product_id, p.product_id, p.product_name, p.product_description, c.color_description, p.typical_selling_price, p.typical_buying_price
FROM dbo.products AS p
JOIN dbo.ref_colors AS c ON p.color_code = c.color_code;

INSERT INTO target.catalog ('id', 'name')
SELECT l.Store_ID, l.Store_Name
FROM dbo.store AS l;
