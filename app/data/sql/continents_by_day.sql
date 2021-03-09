/*Preparing continents_by_day dataset
with cases, deaths, new_cases, new_deaths
by continents by day*/

WITH
    cases AS ( 
        SELECT
			jhu_global_cases.region,
            jhu_global_cases.date,
            sum(jhu_global_cases.cases) AS cases
        FROM jhu_global_cases
        GROUP BY
			jhu_global_cases.date,
			jhu_global_cases.region),
        
    deaths AS (
        SELECT
			jhu_global_deaths.date,
			jhu_global_deaths.region,
            sum(jhu_global_deaths.deaths) AS deaths
        FROM jhu_global_deaths
        GROUP BY
			jhu_global_deaths.date,
			jhu_global_deaths.region),

    cases_deaths AS (
        SELECT
            cases.date,
			cases.region,
            cases.cases,
            deaths.deaths
        FROM cases 
        INNER JOIN deaths
            ON cases.date = deaths.date
			AND cases.region = deaths.region
        ORDER BY cases.date, cases.region),
		
	continents AS (
		SELECT DISTINCT
			country_region,
			continent
		FROM
			jhu_lookup
        WHERE province_state IS NULL)

SELECT
    date,
    CASE
		WHEN continent = 'AF' THEN 'Africa'
		WHEN continent = 'AS' THEN 'Asia'
		WHEN continent = 'EU' THEN 'Europe'
		WHEN continent = 'NA' THEN 'North America'
		WHEN continent = 'OC' THEN 'Oceania'
		WHEN continent = 'SA' THEN 'South America'
		ELSE continent
	END AS continent,
	sum(cases) AS cases,
	sum(deaths) AS deaths,
    sum(cases) - lag(sum(cases))
        OVER(PARTITION BY continent ORDER BY date) AS new_cases,
    sum(deaths) - lag(sum(deaths))
        OVER(PARTITION BY continent ORDER BY date) AS new_deaths
FROM cases_deaths
INNER JOIN continents
	ON cases_deaths.region = continents.country_region
WHERE continent <> 'N/A'
GROUP BY date, continent
