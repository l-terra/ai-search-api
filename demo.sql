CREATE DATABASE demo;

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    FULLTEXT(name)
);

LOAD DATA LOCAL INFILE '//wsl.localhost/Ubuntu/home/cest/ai-search-api/products.csv'
INTO TABLE products
FIELDS TERMINATED BY ','
    ENCLOSED BY """"
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(@dummy, name);

SELECT name FROM products WHERE MATCH(name) AGAINST('tent');

