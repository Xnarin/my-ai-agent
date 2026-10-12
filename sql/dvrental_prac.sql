-- Active: 1791247734535@@127.0.0.1@5432@dvdrental
-- Active: 1791247734535@@127.0.0.1@5432@world
CREATE ROLE dvdrental_reader LOGIN PASSWORD '1234';
GRANT CONNECT ON DATABASE dvdrental TO dvdrental_reader;
GRANT USAGE ON SCHEMA public TO dvdrental_reader;
GRANT SELECT ON category, film_category, film, language, film_actor, actor, staff, rental, inventory, city
TO dvdrental_reader;


-- 기존 reader에서 개인정보 테이블 회수
REVOKE SELECT ON staff, rental FROM dvdrental_reader;

-- 내 대여 내역 전용 역할
DROP ROLE IF EXISTS dvdrental_customer;
CREATE ROLE dvdrental_customer LOGIN PASSWORD '1234';
GRANT CONNECT ON DATABASE dvdrental TO dvdrental_customer;
GRANT USAGE ON SCHEMA public TO dvdrental_customer;
GRANT SELECT ON rental, inventory, film TO dvdrental_customer;

-- rental은 접속할 때 넘긴 customer_id의 행만 보이게
ALTER TABLE rental ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS own_rentals ON rental;
CREATE POLICY own_rentals ON rental
FOR SELECT TO dvdrental_customer
USING (customer_id = current_setting('app.customer_id', true)::int);