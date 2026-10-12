-- Active: 1791247734535@@127.0.0.1@5432@world
CREATE ROLE agent_reader LOGIN PASSWORD '1234';
GRANT CONNECT ON DATABASE world TO agent_reader;
GRANT USAGE ON SCHEMA public TO agent_reader;
GRANT SELECT ON country, city, countrylanguage
TO agent_reader;