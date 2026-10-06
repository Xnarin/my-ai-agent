-- 인구가 800만 이상인 도시의 name, population을 조회하시오

SELECT city.name, city.population 
FROM city
WHERE city.population >= 8000000;

-- 한국(KOR)에 있는 
-- 도시의 
-- name, code를 조회하시오
SELECT name, countrycode 
FROM city
WHERE countrycode = 'KOR'
;
 

-- 유럽 대륙에 속한 
-- 나라들의 
-- name과 region을 조회하시오.
SELECT name, region, continent
FROM country
WHERE continent = 'Europe';
 

-- 이름이 'San'으로 시작하는 
-- 도시의 
-- name을 조회하시오
SELECT name FROM city
WHERE name LIKE 'San%n'
;
 

-- 독립 연도(IndepYear)가 1901년 이상인 
-- 나라의 
-- name, indepyear를 조회하시오.
SELECT name, indepyear 
FROM country
WHERE indepyear > 1900
;
 

-- 인구가 100만에서 200만 사이인 
-- 한국 도시의 
-- name을 조회하시오
SELECT name, population FROM city 
WHERE countrycode = 'KOR'
    AND (population BETWEEN 1000000 AND 2000000);
 

-- 인구가 500만 이상인 
-- 한국, 일본, 중국의 
-- 도시의
-- name, code, population 을 조회하시오
SELECT name, population, countrycode FROM city 
WHERE countrycode IN ('KOR', 'JPN', 'CHN')
    AND population >= 5000000;
 

-- 도시 이름이 'A'로 시작하고 'a'로 끝나는 도시의 name을 조회하시오.
SELECT name FROM city
WHERE name LIKE 'A%a';
 

-- 동남아시아(Southeast Asia) 지역(Region)에 속하지 않는 
-- 아시아(Asia) 대륙 
-- 나라들의 
-- name, region을 조회하시오.
SELECT name, region, continent
FROM country
WHERE continent = 'Asia' 
    AND region != 'Southeast Asia';

SELECT DISTINCT region FROM country WHERE continent = 'Asia';
 

-- 오세아니아(Oceania) 대륙에서 
-- 기대수명의 데이터가 없는 나라의 
-- name, lifeexpectancy, continent를 조회하시오.
-- SELECT DISTINCT continent FROM country;

SELECT name, lifeexpectancy, continent 
FROM country
WHERE continent = 'Oceania'
    AND lifeexpectancy IS NULL;




-- ORDER BY

-- country 테이블에서 
-- 대륙별로 정렬하고, 
-- 같은 대륙 내에서는 GNP가 높은 순으로 정렬하여
--  name, continent, GNP를 조회하시오.
SELECT name, continent, gnp 
FROM country
ORDER BY continent, gnp DESC;
 

-- country 테이블에서 
-- 기대수명이 높은 순으로 정렬하되, 
-- NULL값은 마지막에 나오도록 정렬하여 
-- name, lifeexpectancy를 조회하시오.
SELECT name, lifeexpectancy FROM country
ORDER BY lifeexpectancy DESC NULLS LAST;