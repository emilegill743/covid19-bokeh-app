SELECT
	date,
	region,
	province,
	lat,
	long,
	CASE
		WHEN cases > 0 THEN LOG(1.2,cases)
		ELSE 0
	END AS size,
	cases
FROM jhu_global_cases
WHERE lat <> 0 AND long <> 0