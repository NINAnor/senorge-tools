-- parallel -j32 --bar --joblog log -- uv run senorge_tools den_controls_norway_2019_Blumentrath_NINA.gpkg ::: sd lwc rr tn tg tx ::: {1980..2024}
-- duckdb ':memory:' '.read ../../scripts/den.sql'
create table input_data as (from '*_????.csv');

create table features as (
 select row_number() over () as row_number,
        cat,
        rovbaseid,
        aar,
        lokalitet,
        hi,
        fjellomraade,
        dem_10m_nosefi_float
  from 'den_controls_norway_2019_Blumentrath_NINA.gpkg'
);

create table pivotted as (
  pivot input_data
     on layer using first(value)
  group by row_number, x, y, year, day
);

create table stats as (
with stats as (
     select row_number,
            first(x) as x,
            first(y) as y,
            layer,
            year,
            min(value) as "min",
            avg(value) as "avg",
            max(value) as "max",
            var_pop(value) as "varpop"
      from input_data
     group by row_number, year, layer
), unpivoted as (
     select row_number,
            x,
            y,
            layer || '_' || year || '_' || param_name as layer_year,
            param_value
       from stats
    unpivot (param_value for param_name in ("min", "avg", "max", "varpop"))
)
  pivot unpivoted on layer_year
  using first(param_value)
  group by row_number, x, y
);

copy (
 select x,
        y,
        features.*,
        columns(x -> x similar to 'sd_.*'),
        columns(x -> x similar to 'lwc_.*'),
        columns(x -> x similar to 'rr_.*'),
   from stats
   join features using (row_number)
  order by row_number
) to 'den_sd_lwc_rr.csv' (header, delimiter ',');

copy (
 select x,
        y,
        features.*,
        columns(x -> x similar to 'tn_.*'),
        columns(x -> x similar to 'tg_.*'),
        columns(x -> x similar to 'tx_.*'),
   from stats
   join features using (row_number)
  order by row_number
) to 'den_tn_tg_tx.csv' (header, delimiter ',');

copy (
with stats as (
 select row_number,
        first(x) as x,
        first(y) as y,
        year,
        sum(case when sd > 0 then 1 else 0 end) as days_with_snow,
        sum(case when tg > 0 then 1 else 0 end) as days_with_avg_tg_above_0,
        sum(case when tg > 5 then 1 else 0 end) as days_with_avg_tg_above_5,
        sum(case when rr > 0 and sd > 0 then 1 else 0 end) as days_with_rr_and_sd_above_0
   from pivotted
  group by row_number, year
), unpivoted as (
     select row_number,
            x,
            y,
            param_name || '_' || year  as param_year,
            param_value
       from stats
    unpivot (param_value for param_name in ("days_with_snow", "days_with_avg_tg_above_0", "days_with_avg_tg_above_5", "days_with_rr_and_sd_above_0"))
), pivoted as (
  pivot unpivoted on param_year
  using first(param_value)
  group by row_number, x, y
  order by row_number
)
   from pivoted
   join features using (row_number)
) to 'den_extra.csv' (header, delimiter ',');
