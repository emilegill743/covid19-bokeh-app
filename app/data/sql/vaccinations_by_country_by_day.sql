with continents AS (
	SELECT DISTINCT
		iso3,
		continent
	FROM
		jhu_lookup
    WHERE province_state IS NULL)

SELECT
	location,
	CASE
		WHEN location = 'Jersey' THEN 'Europe'
		WHEN location = 'Guernsey' THEN 'Europe'
		WHEN continent = 'AF' THEN 'Africa'
		WHEN continent = 'AS' THEN 'Asia'
		WHEN continent = 'EU' THEN 'Europe'
		WHEN continent = 'NA' THEN 'North America'
		WHEN continent = 'OC' THEN 'Oceania'
		WHEN continent = 'SA' THEN 'South America'
		ELSE continent
	END AS continent,
	date,
	max(total_vaccinations)
		OVER (PARTITION BY location
			  ORDER BY date ROWS BETWEEN
			  UNBOUNDED PRECEDING AND CURRENT ROW
			 ) AS total_vaccinations,
	people_vaccinated,
	people_fully_vaccinated,
	daily_vaccinations,
	total_vaccinations_per_hundred,
	people_vaccinated_per_hundred,
	people_fully_vaccinated_per_hundred,
	daily_vaccinations_per_million
FROM
	owid_global_vaccinations
	LEFT JOIN
	continents
	ON owid_global_vaccinations.iso_code = continents.iso3
WHERE
	owid_global_vaccinations.iso_code IS NOT NULL
	AND
	owid_global_vaccinations.iso_code NOT LIKE 'OWID_%%'
ORDER BY location, date
