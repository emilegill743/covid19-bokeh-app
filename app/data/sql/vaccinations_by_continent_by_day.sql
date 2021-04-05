SELECT
	owid.location AS continent,
	owid.date,
	max(total_vaccinations)
		OVER (PARTITION BY owid.location
			  ORDER BY owid.date ROWS BETWEEN
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
	owid_global_vaccinations AS owid
WHERE
	owid.location IN ('Asia', 'Africa', 'Europe', 'North America', 'South America', 'Oceania')
ORDER BY
	owid.location,
	owid.date
