-- duckdb ':memory:' '.read ../../scripts/group_by_month.sql'
copy (
    with data_month_precision as (
        select
            *,
            datetrunc('month', make_date("year", 1, 1) + interval ("day") days) as year_month
        from 'extracted/*.csv'
    )
    select
        year_month, x, y,
        min(sd), avg(sd), max(sd), var_pop(sd),
        min(rr), avg(rr), max(rr), var_pop(rr),
        min(tg), avg(tg), max(tg), var_pop(tg)
    from
        data_month_precision
    group by
        x, y, year_month
) to 'monthly_average.csv' (header, delimiter ',')
;
