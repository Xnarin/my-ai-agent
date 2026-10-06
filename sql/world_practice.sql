-- Active: 1791247734535@@127.0.0.1@5432@world
SELECT city.name as cityname,
       country.name as countryname,
       country.continent
FROM city
INNER JOIN country ON city.countrycode = country.code;

SELECT
    co.name AS country_name,
    ci.name AS capital_city,
    cl."Language"
FROM country co
JOIN city ci ON co.capital = ci.id
JOIN countrylanguage cl ON co.code = cl.countrycode
WHERE cl.isofficial = 'T';