WITH new_cases_cte AS (
	SELECT
		date,
		region,
		province,
		lat,
		long,
		cases - lag(cases)
			OVER( PARTITION BY
					region, province
				  ORDER BY
				  	region, province, date
				) AS new_cases
	FROM jhu_global_cases
)
SELECT *,
	CASE
		WHEN new_cases > 0 THEN LOG(1.2,new_cases)
		ELSE 0
	END AS size
FROM new_cases_cte
WHERE lat <> 0 AND long <> 0
