"""Validated historical time series and reproducible descriptive reporting."""
from pathlib import Path
import pandas as pd

DATA_PATH = Path(__file__).parent / 'data' / 'us.csv'


def load_data(path=DATA_PATH):
    frame = pd.read_csv(path)
    if not {'date', 'cases', 'deaths'} <= set(frame.columns):
        raise ValueError('CSV must contain date, cases, and deaths.')
    frame = frame[['date', 'cases', 'deaths']].copy()
    frame['date'] = pd.to_datetime(frame['date'], errors='raise')
    if frame.empty or frame.isna().any().any() or frame['date'].duplicated().any():
        raise ValueError('Data must be nonempty, complete, and have unique dates.')
    for metric in ['cases', 'deaths']:
        frame[metric] = pd.to_numeric(frame[metric], errors='raise')
        if (frame[metric] < 0).any() or (frame[metric] % 1 != 0).any():
            raise ValueError('Cumulative counts must be nonnegative integers.')
    frame = frame.sort_values('date').reset_index(drop=True)
    if not frame['date'].diff().iloc[1:].eq(pd.Timedelta(days=1)).all():
        raise ValueError('Daily dates must be contiguous; missing days are not zeros.')
    for metric in ['cases', 'deaths']:
        # Unknown pre-snapshot baseline remains missing, never assumed to be zero.
        frame[f'new_{metric}'] = frame[metric].diff()
        frame[f'{metric}_7d'] = frame[f'new_{metric}'].rolling(7, min_periods=7).mean()
    return frame


def select_range(frame, start=None, end=None):
    first = pd.Timestamp(start) if start else frame.date.min()
    last = pd.Timestamp(end) if end else frame.date.max()
    if pd.isna(first) or pd.isna(last) or first.tzinfo or last.tzinfo:
        raise ValueError('Use calendar dates in YYYY-MM-DD format.')
    if first > last:
        raise ValueError('Start date must be before or equal to end date.')
    result = frame.loc[frame.date.between(first, last)].copy()
    if result.empty:
        raise ValueError('No observations in this date range.')
    return result


def summarize(frame):
    cases_peak = frame.dropna(subset=['cases_7d'])
    deaths_peak = frame.dropna(subset=['deaths_7d'])
    last = frame.iloc[-1]
    def peak(rows, metric):
        if rows.empty:
            return None
        row = rows.loc[rows[f'{metric}_7d'].idxmax()]
        return {'date': row.date.strftime('%Y-%m-%d'), 'value': round(float(row[f'{metric}_7d']), 1)}
    return {
        'start': frame.date.min().strftime('%Y-%m-%d'),
        'end': frame.date.max().strftime('%Y-%m-%d'),
        'observations': len(frame),
        'cumulative_cases': int(last.cases),
        'cumulative_deaths': int(last.deaths),
        'net_new_cases': int(frame.new_cases.sum()),
        'net_new_deaths': int(frame.new_deaths.sum()),
        'case_peak': peak(cases_peak, 'cases'),
        'death_peak': peak(deaths_peak, 'deaths'),
        'correction_days': int(((frame.new_cases < 0) | (frame.new_deaths < 0)).sum()),
        'unknown_baseline_days': int(frame.new_cases.isna().sum()),
    }


def monthly_summary(frame):
    return frame.set_index('date')[['new_cases', 'new_deaths']].resample('MS').sum(min_count=1).reset_index()


def write_report(output='reports/analysis.md'):
    frame = load_data()
    result = summarize(frame)
    peak = result['case_peak']
    deaths = result['death_peak']
    text = f'''# COVID-19 historical reporting: United States

Source: The New York Times, `us.csv`; historical snapshot {result['start']} to {result['end']}.

## Findings

- Analyzed {result['observations']:,} daily observations.
- End-of-snapshot cumulative reported cases: {result['cumulative_cases']:,}.
- End-of-snapshot cumulative reported deaths: {result['cumulative_deaths']:,}.
- Highest trailing seven-day mean of net new reported cases: {peak['value']:,.1f} on {peak['date']}.
- Highest trailing seven-day mean of net new reported deaths: {deaths['value']:,.1f} on {deaths['date']}.
- {result['correction_days']} days have a negative net change in cases or deaths, indicating revisions.

## Method

Pandas validates and sorts the cumulative time series. Daily net reports are successive differences. Negative corrections remain in the data. Seven-day means require seven valid daily differences and are calculated before date filtering, retaining prior-day context. The first daily difference is unknown and stays missing. Monthly totals sum daily differences; partial months are labeled in the dashboard. Totals for a selected interval include the difference on its first day when the preceding observation is available.

## Interpretation and limitations

These are reports by date, not infection or death occurrence dates. Testing, reporting schedules, backlog releases, case definitions, and revisions influence patterns. Counts include confirmed and probable cases; the source includes U.S. territories and the District of Columbia. Reported cases undercount infections. No causal claims, forecasts, or medical recommendations are made. National totals are not adjusted for population. This archived dataset does not describe current conditions. The first observation has no preceding baseline; its one case is excluded from net-change totals.

## Reproduce

Run `python report.py` from the repository root. The CSV checksum and source attribution are recorded in `data/README.md`. This report is generated from the bundled data, without network access.
'''
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(text)
    return text
