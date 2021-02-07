SELECT
	date,
	area_name,
	area_code,
	new_cases,
	cum_cases,
	SUM(new_cases)
		OVER(PARTITION BY area_code
			 ORDER by date
			 ROWS BETWEEN 6 PRECEDING
			 AND current ROW) AS weekly_cases,
	AVG(new_cases)
		OVER(PARTITION BY area_code
			 ORDER by date
			 ROWS BETWEEN 6 PRECEDING
			 AND current ROW) AS weekly_average
FROM local_uk

