-- Active: 1791247734535@@127.0.0.1@5432@dvdrental
--고객의 이름과 대여일을 조회하시오.
SELECT 
customer.first_name as first_name,
customer.last_name as last_name,
rental.rental_date as rentaldate
FROM customer
JOIN rental ON customer.customer_id = rental.customer_id
; 

--배우의 이름과 해당 배우가 출연한 영화의 제목을 조회하시오.
SELECT 
actor.first_name as first_name,
actor.last_name as last_name,
film.title as filmtitle
FROM actor
INNER JOIN film_actor ON actor.actor_id = film_actor.actor_id
INNER JOIN film ON film_actor.film_id = film.film_id;

--first_name이 'Penelope'인 배우가 출연한 영화의 제목을 조회하시오.
SELECT 
actor.first_name as first_name,
actor.last_name as last_name,
film.title as filmtitle
FROM actor
INNER JOIN film_actor ON actor.actor_id = film_actor.actor_id
INNER JOIN film ON film_actor.film_id = film.film_id
WHERE first_name = 'Penelope';

--배우들이 출연한 영화의 등급을 중복 없이 조회하시오.
SELECT DISTINCT
actor.first_name as first_name,
actor.last_name as last_name,
film.rating as rating
FROM actor
INNER JOIN film_actor ON actor.actor_id = film_actor.actor_id
INNER JOIN film ON film_actor.film_id = film.film_id

--배우별로 출연한 영화의 등급을 중복 없이 조회하시오. (배우 ID, 이름(first_name, last_name), 등급)
SELECT DISTINCT
actor.actor_id as actor_id,
actor.first_name as first_name,
actor.last_name as last_name,
film.rating as rating
FROM actor
INNER JOIN film_actor ON actor.actor_id = film_actor.actor_id
INNER JOIN film ON film_actor.film_id = film.film_id

--고객의 이름과 해당 고객이 대여한 영화의 제목을 조회하시오.
SELECT 
customer.first_name as first_name,
customer.last_name as last_name,
film.title as title
FROM customer
JOIN rental ON customer.customer_id = rental.customer_id
JOIN inventory ON rental.inventory_id = inventory.inventory_id
JOIN film ON inventory.film_id = film.film_id
; 

--'Yentl Idaho' 영화를 대여한 고객 정보를 중복 없이 조회하시오.
--직원의 이름과 근무하는 매장의 주소, 도시를 조회하시오.
--고객별로 대여한 영화의 제목, 지불한 금액, 대여일을 조회하시오.
--'Action' 카테고리의 영화에 출연한 배우를 중복 없이 조회하시오.
--출연 배우가 있는 영화별로 배우 수를 조회하시오.
--출연 배우 수가 5명 초과인 영화와 배우 수를 배우 수 내림차순으로 정렬하여 조회하시오.
--카테고리별 평균 대여료를 조회하시오.
--고객이 있는 국가별로 고객 수를 조회하시오.
--고객 ID가 1인 고객이 가장 많이 대여한 영화의 카테고리를 조회하시오.
--재고(inventory)에 등록되지 않은 영화를 조회하시오.