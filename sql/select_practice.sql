-- Active: 1791247734535@@127.0.0.1@5432@dvdrental
--1 
SELECT title, rental_rate
FROM film;

--2
SELECT title, rental_rate
FROM film
WHERE rental_rate >= 4;

--3
SELECT title
FROM film
WHERE title ILIKE 'angel%l';

--4
SELECT title, rental_duration, rental_rate
FROM film
WHERE rental_duration >= 5 AND rental_rate >= 4;

--5
SELECT title, rating, rental_duration
FROM film
WHERE rating in ('G', 'PG');

--6
SELECT title, length
FROM film
WHERE (length BETWEEN 60 AND 80)
ORDER BY length ASC;

--7
SELECT title, rating 
FROM film
WHERE rating = 'R'
ORDER BY title ASC;

--8
SELECT DISTINCT length
FROM film
ORDER BY length ASC
LIMIT 10 OFFSET 0;

--9
SELECT DISTINCT title, length
FROM film
ORDER BY length DESC, title ASC
LIMIT 6 OFFSET 9;

--10
SELECT rating, COUNT(*)
from film
GROUP BY rating

--11
SELECT rental_duration, COUNT(*)
from film
GROUP BY rental_duration

--12
SELECT rating, COUNT(*), AVG(length)
from film
GROUP BY rating

--13
SELECT replacement_cost, COUNT(*), AVG(rental_rate)
FROM film
GROUP BY replacement_cost
ORDER BY replacement_cost ASC

--14
SELECT rental_rate, COUNT(*) as count
FROM film
GROUP BY rental_rate
ORDER BY count ASC

--15
SELECT rating, AVG(rental_rate)
FROM film
GROUP BY rating
HAVING AVG(rental_rate) < 3 
