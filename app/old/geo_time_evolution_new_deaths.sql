WITH new_deaths_cte AS (
	SELECT
		date,
		region,
		province,
		lat,
		long,
		deaths - lag(deaths)
			OVER( PARTITION BY
					region, province
				  ORDER BY
				  	region, province, date
				  ) AS new_deaths
	FROM jhu_global_deaths	
)
SELECT *,
	CASE
		WHEN new_deaths > 0 THEN LOG(1.2,new_deaths)
		ELSE 0
	END AS size
FROM new_deaths_cte
WHERE lat <> 0 AND long <> 0
