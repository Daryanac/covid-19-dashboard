# COVID-19 historical reporting: United States

Source: The New York Times, `us.csv`; historical snapshot 2020-01-21 to 2023-03-23.

## Findings

- Analyzed 1,158 daily observations.
- End-of-snapshot cumulative reported cases: 103,910,034.
- End-of-snapshot cumulative reported deaths: 1,135,343.
- Highest trailing seven-day mean of net new reported cases: 806,927.9 on 2022-01-14.
- Highest trailing seven-day mean of net new reported deaths: 3,351.7 on 2021-01-12.
- 5 days have a negative net change in cases or deaths, indicating revisions.

## Method

Pandas validates and sorts the cumulative time series. Daily net reports are successive differences. Negative corrections remain in the data. Seven-day means require seven valid daily differences and are calculated before date filtering, retaining prior-day context. The first daily difference is unknown and stays missing. Monthly totals sum daily differences; partial months are labeled in the dashboard. Totals for a selected interval include the difference on its first day when the preceding observation is available.

## Interpretation and limitations

These are reports by date, not infection or death occurrence dates. Testing, reporting schedules, backlog releases, case definitions, and revisions influence patterns. Counts include confirmed and probable cases; the source includes U.S. territories and the District of Columbia. Reported cases undercount infections. No causal claims, forecasts, or medical recommendations are made. National totals are not adjusted for population. This archived dataset does not describe current conditions. The first observation has no preceding baseline; its one case is excluded from net-change totals.

## Reproduce

Run `python report.py` from the repository root. The CSV checksum and source attribution are recorded in `data/README.md`. This report is generated from the bundled data, without network access.
