import io
import pandas as pd
import pytest
from analysis import load_data, select_range, summarize
from app import app


def test_real_snapshot_and_first_difference():
    frame = load_data()
    assert frame.date.min() == pd.Timestamp('2020-01-21')
    assert frame.date.max() == pd.Timestamp('2023-03-23')
    assert pd.isna(frame.new_cases.iloc[0])
    assert frame.new_cases.sum() == frame.cases.iloc[-1] - frame.cases.iloc[0]


def test_rolling_context_is_retained():
    frame = load_data()
    filtered = select_range(frame, '2022-01-01', '2022-01-01')
    expected = frame.loc[frame.date.between('2021-12-26', '2022-01-01'), 'new_cases'].mean()
    assert filtered.cases_7d.iloc[0] == pytest.approx(expected)


def test_corrections_are_not_clipped(tmp_path):
    path = tmp_path / 'series.csv'
    pd.DataFrame({'date':pd.date_range('2020-01-01',periods=9), 'cases':[0,10,20,30,40,50,60,55,80], 'deaths':[0]*9}).to_csv(path,index=False)
    frame = load_data(path)
    assert frame.new_cases.iloc[7] == -5
    assert summarize(frame)['correction_days'] == 1


def test_rejects_gaps_and_duplicate_dates(tmp_path):
    path = tmp_path / 'series.csv'
    for dates in [['2020-01-01','2020-01-03'], ['2020-01-01','2020-01-01']]:
        pd.DataFrame({'date':dates,'cases':[1,2],'deaths':[0,0]}).to_csv(path,index=False)
        with pytest.raises(ValueError):
            load_data(path)


def test_dashboard_and_filtered_export():
    client = app.test_client()
    assert client.get('/').status_code == 200
    result = client.get('/api/dashboard?start=2022-01-01&end=2022-01-31&metric=deaths')
    assert result.status_code == 200
    assert result.json['summary']['observations'] == 31
    assert len(result.json['figures']) == 3
    csv = client.get('/export.csv?start=2022-01-01&end=2022-01-31')
    frame = pd.read_csv(io.StringIO(csv.text))
    assert len(frame) == 31
    assert frame.date.iloc[0] == '2022-01-01'
    assert frame.cases_7d.notna().all()


@pytest.mark.parametrize('query', ['start=nope','start=2024-01-01','start=2022-02-01&end=2022-01-01','metric=invalid','end=2022-02-30','start=NaT'])
def test_bad_filters(query):
    assert app.test_client().get('/api/dashboard?' + query).status_code == 400


def test_local_plotly_and_health():
    client = app.test_client()
    assert client.get('/plotly.js').status_code == 200
    assert client.get('/health').json['status'] == 'ok'
