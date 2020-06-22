SELECT
	region,
	rank()
		OVER (PARTITION BY region
			  ORDER BY date)
		AS days_since_arrival,
	cases
FROM
	(SELECT region, date, sum(cases) AS cases
	 FROM jhu_global_cases
	 GROUP BY region, date) AS subquery
WHERE cases > 100;
