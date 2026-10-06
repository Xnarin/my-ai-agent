-- 대륙별 총 인구수를 구하시오.
 SELECT continent, SUM(population) AS total_population
 FROM country
 GROUP BY continent
 ORDER BY total_population DESC ;

-- 대륙별 
-- 평균 GNP와 
-- 평균 인구를 구하시오.
SELECT continent, AVG(gnp), AVG(population)
FROM country
GROUP BY continent;
 

-- 인구가 50만 이상 100만 이하인 
-- 도시들을 대상으로, 
-- CountryCode와 District별 
-- 도시 수를 구하시오.
SELECT countrycode, district, count(*)
FROM city
WHERE population BETWEEN 500000 AND 1000000
GROUP BY countrycode, district
;
 

-- 아시아 대륙 
-- 국가들의 
-- Region별 
-- 총 GNP를 구하시오.
SELECT region, SUM(gnp) total_gnp
FROM country
WHERE continent = 'Asia'
GROUP BY region;
 

-- 대륙별 
-- 국가 수가 많은 순서대로 
-- Continent, 국가 수를 조회하시오.
SELECT continent, COUNT(*)
FROM country
GROUP BY continent
ORDER BY COUNT(*) DESC;
 
SELECT continent, COUNT(*) AS country_count
FROM country
GROUP BY continent
ORDER BY country_count DESC;


-- 독립년도가 있는 국가들의 
-- 대륙별 
-- 평균 기대수명이 높은 순서대로 
-- Continent, 평균 기대수명을 조회하시오.
SELECT continent, AVG(lifeexpectancy) as avg_life
FROM country
WHERE indepyear IS NOT NULL
GROUP BY continent
ORDER BY avg_life DESC;
 

-- Region별 
-- 총 GNP를 구하고, 
-- 총 GNP가 가장 높은 Region을 조회하시오. (GNP: 국민 총생산)
SELECT region, sum(gnp) as total_gnp
FROM country
GROUP BY region
ORDER BY total_gnp DESC
LIMIT 1;


SELECT continent, COUNT(*) AS country_count
FROM country
GROUP BY continent
HAVING COUNT(*) > 20
ORDER BY country_count DESC


-- 인구가 1000만 이상인 
-- 국가의 수가 
-- 10개가 넘는 
-- 대륙의 이름과 국가 수 조회
-- 

SELECT continent, count(*)
FROM country
WHERE population >= 10000000
GROUP BY continent
HAVING count(*) > 10;