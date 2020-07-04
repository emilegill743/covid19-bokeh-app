/*Preparing global time evolution dataset
with cases, deaths, new_cases, new_deaths
for each geographical province*/

-- Combining global cases with US cases by state
WITH cases AS (
	SELECT * FROM jhu_global_cases
	WHERE region <> 'US'
	UNION
	SELECT
		jhu_us_cases.region,
		jhu_us_cases.province,
		us_states_coords."Latitude" AS lat,
		us_states_coords."Longitude" AS long,
		jhu_us_cases.date,
		jhu_us_cases.cases
	FROM jhu_us_cases
	-- Mapping to state latitude/longitude
	-- in us_states_coords table
	INNER JOIN us_states_coords
	ON jhu_us_cases.province = us_states_coords."City"
	),
	
-- Combining global deaths with US deaths by state
deaths AS (
	SELECT * FROM jhu_global_deaths
	WHERE region <> 'US'
	UNION
	SELECT
		jhu_us_deaths.region,
		jhu_us_deaths.province,
		us_states_coords."Latitude" AS lat,
		us_states_coords."Longitude" AS long,
		jhu_us_deaths.date,
		jhu_us_deaths.deaths
	FROM jhu_us_deaths
	-- Mapping to state latitude/longitude
	-- in us_states_coords table
	INNER JOIN us_states_coords
	ON jhu_us_deaths.province = us_states_coords."City"
	),
	
-- Joining cases and deaths datasets
cases_deaths AS (
	SELECT
		cases.region,
		cases.province,
		cases.lat,
		cases.long,
        cases.date,
        cases.cases AS cases,
        deaths.deaths AS deaths
    FROM cases
    INNER JOIN deaths
    ON
        cases.date = deaths.date
        AND
        cases.region = deaths.region
        AND
        cases.province = deaths.province
        AND
        cases.lat = deaths.lat
        AND
        cases.long = deaths.long)
-- Calculating daily new cases/deaths
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
FROM cases_deaths
-- Filtering out non-geographical locations
WHERE lat <> 0  AND long <> 0