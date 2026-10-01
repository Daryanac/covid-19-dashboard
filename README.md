# COVID-19 Data Reporting & Visualization

An interactive Python dashboard that turns historical U.S. COVID-19 reporting into explorable trends and reproducible findings. Built with **Pandas, Flask, and Plotly** for a data analysis portfolio.

## Explore

- Switch between reported cases and deaths.
- Filter any date interval in the bundled January 21, 2020–March 23, 2023 snapshot.
- Explore daily net reports, trailing seven-day averages, cumulative counts, and monthly totals.
- Hover, zoom, pan, and save Plotly charts as images.
- Export the selected interval, including calculated metrics, to CSV.
- Reproduce the written [analysis report](reports/analysis.md).

The application runs offline after dependencies are installed: both the source snapshot and Plotly JavaScript are served locally.

## Run locally

Requires Python 3.11+ (CI uses 3.12).

```bash
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000**.

For a production WSGI server:

```bash
gunicorn --bind 0.0.0.0:8000 app:app
```

The `Procfile` supports hosts that run Python web services. This repository does not include a hosted live deployment.

## Reproduce the analysis

```bash
python report.py
pip install -r requirements-dev.txt
python -m pytest -q
```

GitHub Actions runs the tests and verifies the committed report matches its generated output.

## Findings from the bundled snapshot

Across 1,158 daily observations, the highest trailing seven-day mean of net new reported cases was **806,927.9 on January 14, 2022**. The corresponding peak for reported deaths was **3,351.7 on January 12, 2021**. Five observations contain a downward revision in cases or deaths. See the report for the calculation and interpretation.

## Data pipeline and choices

`data/us.csv` → validation with Pandas → daily differences → trailing means and monthly aggregation → Flask JSON endpoints → interactive Plotly figures.

- Input dates must be unique, complete, and contiguous. Counts must be nonnegative integers.
- Negative daily differences represent revisions and remain in both plots and aggregates.
- The first difference is missing because no prior baseline exists; it is never fabricated as zero.
- Rolling averages require seven valid daily differences and are computed on the full snapshot before filtering.
- Summary cards explicitly distinguish cumulative totals at the interval end from net reports within the interval.
- Monthly totals sum net reports within the selected dates; edge months can be partial.
- Invalid filters return HTTP 400 and an actionable UI message.

## API

| Endpoint | Response |
| --- | --- |
| `GET /api/dashboard?start=2022-01-01&end=2022-01-31&metric=cases` | Summary metrics and three Plotly figures |
| `GET /export.csv?start=2022-01-01&end=2022-01-31` | Filtered observations and derived columns |
| `GET /health` | Application status and observation count |

Dates use `YYYY-MM-DD`; the metric is `cases` or `deaths`. Omitted dates use the full snapshot. All calculations are descriptive; no population normalization, forecasting, or causal inference is implemented.

## Project structure

```text
app.py                 Flask routes and Plotly figures
analysis.py            Data validation, transformation, reporting
report.py              Reproducible Markdown report command
data/                  Bundled source snapshot, provenance, data license
static/                Responsive CSS and dashboard JavaScript
templates/             Dashboard HTML
reports/               Generated findings and methods
tests/                 Data integrity and API regression tests
.github/workflows/     Automated Python checks
```

## Source, scope, and license

Data: **The New York Times**, [Coronavirus (COVID-19) Data in the United States](https://github.com/nytimes/covid-19-data), `us.csv`. The source stopped daily updates in March 2023. This is historical data, not a current COVID-19 monitor.

The source includes U.S. territories and the District of Columbia and combines confirmed and probable cases. Testing, definitions, backlog releases, reporting schedules, and revisions affect reported counts. Reports do not establish infection dates or causal effects. See [data provenance](data/README.md) and the [source's data license](data/LICENSE-NYT.txt).

Original application code is MIT licensed. **The bundled NYT data and outputs derived from it retain the source's separate non-commercial attribution license.** This project is intended for non-commercial educational and portfolio use.
