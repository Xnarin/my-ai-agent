SELECT * FROM country;
SELECT name, continent from country;

SELECT country.name, country.continent FROM country

SELECT c.name, c.continent FROM country as c;

SELECT 
    c.name as 국가명, 
    c.continent as 대륙명 
FROM country as c;

SELECT 
    c.name "국가 명", 
    c.continent 대륙명 
FROM country c;

-- 중복제거
SELECT DISTINCT continent, region FROM country;


-- select

SELECT country.name, country.continent, country.population
FROM country
WHERE population > 1000000
  AND (continent = 'Asia' OR continent = 'Europe');

SELECT name, population
FROM city
ORDER BY population DESC;


SELECT name, countrycode, population
FROM city
ORDER BY countrycode , population DESC;


SELECT name, indepyear FROM country
-- WHERE indepyear is not null
ORDER BY indepyear DESC NULLS LAST;

SELECT name, indepyear FROM country
-- WHERE indepyear is not null
ORDER BY indepyear NULLS FIRST;




SELECT name, population
FROM city
ORDER BY population DESC
LIMIT 10; -- OFFSET 0 생략


SELECT name, population
FROM city
ORDER BY population DESC
LIMIT 5 OFFSET 10;


SELECT name, population
FROM city
ORDER BY population DESC
LIMIT 20;

-- city 테이블에서 
-- 인구수가 가장 적은 도시 
-- 5개를 조회하시오.
SELECT name, population 
FROM city
ORDER BY population
LIMIT 5;
 

-- country 테이블에서 
-- 면적(surfacearea)이 가장 넓은 순서대로 
-- 11위부터 20위까지의 
-- 국가를 조회하시오.
SELECT name, surfacearea 
FROM country
ORDER BY surfacearea DESC
LIMIT 10 OFFSET 10;

SELECT name, surfacearea 
FROM country
ORDER BY surfacearea DESC;

-- country 테이블에서 
-- 기대수명이 높은 순서대로 
-- 1위부터 5위까지의 국가를 조회하시오.

SELECT name, lifeexpectancy FROM country
ORDER BY lifeexpectancy DESC NULLS LAST
LIMIT 5;


SELECT continent, name, COUNT(*) AS country_count
FROM country
GROUP BY continent;

SELECT region, AVG(population) AS avg_pop
FROM country
GROUP BY region;


SELECT region, COUNT(*) AS country_count
FROM country
WHERE continent = 'Asia'
GROUP BY region;

SELECT continent, governmentform, COUNT(*)
FROM country
GROUP BY continent, governmentform
ORDER BY continent, governmentform;