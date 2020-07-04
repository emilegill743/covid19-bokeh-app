SELECT
	date,
	region,
	province,
	lat,
	long,
	CASE
		WHEN deaths > 0 THEN LOG(1.2,deaths)
		ELSE 0
	END AS size,
	deaths
FROM jhu_global_deaths
WHERE lat <> 0 AND long <> 0