/*Preparing global_by_day dataset
with cases, deaths, new_cases, new_deaths
by day*/

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

    cases_deaths AS (
        SELECT
            cases.date,
            cases.cases,
            deaths.deaths
        FROM cases 
        INNER JOIN deaths
            ON cases.date = deaths.date
        ORDER BY cases.date)

SELECT
    date, cases, deaths,
    cases - lag(cases)
        OVER(ORDER BY date) AS new_cases,
    deaths - lag(deaths)
        OVER(ORDER BY date) AS new_deaths
FROM cases_deaths

