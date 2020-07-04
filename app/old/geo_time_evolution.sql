SELECT
    date, region, province, lat, long, cases, deaths,
    cases - lag(cases)
        OVER( PARTITION BY region, province
			  ORDER BY region, province, date
			) AS new_cases,
    deaths - lag(deaths)
        OVER( PARTITION BY region, province
			  ORDER BY region, province, date
			) AS new_deaths
FROM (
    SELECT
		jhu_global_cases.region,
		jhu_global_cases.province,
		jhu_global_cases.lat,
		jhu_global_cases.long,
        jhu_global_cases.date,
        sum(jhu_global_cases.cases) AS cases,
        sum(jhu_global_deaths.deaths) AS deaths
    FROM jhu_global_cases
    INNER JOIN jhu_global_deaths
    ON
        jhu_global_cases.date = jhu_global_deaths.date
        AND
        jhu_global_cases.region = jhu_global_deaths.region
        AND
        jhu_global_cases.province = jhu_global_deaths.province
        AND
        jhu_global_cases.lat = jhu_global_deaths.lat
        AND
        jhu_global_cases.long = jhu_global_deaths.long
    GROUP BY
		jhu_global_cases.region,
		jhu_global_cases.province,
		jhu_global_cases.lat,
		jhu_global_cases.long,
        jhu_global_cases.date) AS subquery
WHERE lat <> 0  AND long <> 0
