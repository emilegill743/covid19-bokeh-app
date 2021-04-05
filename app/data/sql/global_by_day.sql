/*Preparing global_by_day dataset
with cases, deaths, new_cases, new_deaths
and vaccinations stats by day*/

WITH 
    cases AS ( 
        SELECT
            jhu_global_cases.date,
            sum(jhu_global_cases.cases) AS cases
        FROM jhu_global_cases
        GROUP BY jhu_global_cases.date),
        
    deaths AS (
        SELECT jhu_global_deaths.date,
            sum(jhu_global_deaths.deaths) AS deaths
        FROM jhu_global_deaths
        GROUP BY jhu_global_deaths.date),
		
	vaccinations AS (
		SELECT
			date,
			total_vaccinations,
			people_vaccinated,
			people_fully_vaccinated,
			daily_vaccinations,
			total_vaccinations_per_hundred,
			people_vaccinated_per_hundred,
			people_fully_vaccinated_per_hundred,
			daily_vaccinations_per_million
		FROM owid_global_vaccinations
		WHERE location = 'World'
		ORDER BY date)

SELECT
	cases.date,
	cases.cases,
	cases.cases - lag(cases.cases)
		OVER(ORDER BY cases.date) AS new_cases,
	deaths.deaths,
	deaths - lag(deaths)
		OVER(ORDER BY cases.date) AS new_deaths,
	vaccinations.total_vaccinations,
	vaccinations.people_vaccinated,
	vaccinations.people_fully_vaccinated,
	vaccinations.daily_vaccinations,
	vaccinations.total_vaccinations_per_hundred,
	vaccinations.people_vaccinated_per_hundred,
	vaccinations.people_fully_vaccinated_per_hundred,
	vaccinations.daily_vaccinations_per_million
FROM cases
INNER JOIN deaths
	ON cases.date = deaths.date
LEFT JOIN vaccinations
	ON cases.date = vaccinations.date
ORDER BY cases.date
