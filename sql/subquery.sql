-- Active: 1791247734535@@127.0.0.1@5432@world
SELECT c.name, c.countrycode, c.population
FROM city AS c
WHERE c.population = (
    SELECT MAX(c2.population)
    FROM city AS c2
);

SELECT c.name, c.countrycode, c.population

FROM city AS c

WHERE c.population = (

    SELECT MAX(c2.population)

    FROM city AS c2

    WHERE c2.countrycode = c.countrycode

);



