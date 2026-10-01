"""Flask dashboard, Plotly figures, and filtered CSV export."""
import json
import re
from flask import Flask, Response, jsonify, render_template, request
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
from plotly.offline import get_plotlyjs
from analysis import load_data, monthly_summary, select_range, summarize

app = Flask(__name__)
DATA = load_data()


def selected():
    for name in ('start', 'end'):
        value = request.args.get(name)
        if value and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            raise ValueError('Dates must use YYYY-MM-DD format.')
    return select_range(DATA, request.args.get('start'), request.args.get('end'))


def figures(frame):
    metric = request.args.get('metric', 'cases')
    if metric not in ('cases', 'deaths'):
        raise ValueError('Metric must be cases or deaths.')
    color = '#46d6b0' if metric == 'cases' else '#a798ff'
    dates = frame.date.dt.strftime('%Y-%m-%d').tolist()
    daily = go.Figure([
        go.Bar(x=dates, y=frame[f'new_{metric}'].tolist(), name='Daily net reports', marker_color=color, opacity=.3),
        go.Scatter(x=dates, y=frame[f'{metric}_7d'].tolist(), name='Trailing 7-day average', line={'color':color, 'width':3}),
    ])
    cumulative = go.Figure(go.Scatter(x=dates, y=frame[metric].tolist(), name=f'Cumulative {metric}', fill='tozeroy', line={'color':color}))
    monthly = monthly_summary(frame)
    monthly_fig = go.Figure(go.Bar(x=monthly.date.dt.strftime('%b %Y').tolist(), y=monthly[f'new_{metric}'].tolist(), marker_color=color, name='Net reports'))
    result = []
    for fig, title in [(daily, f'Daily reported {metric}'), (cumulative, f'Cumulative reported {metric}'), (monthly_fig, f'Monthly net reported {metric} · edge months may be partial')]:
        fig.update_layout(title=title, template='plotly_dark', paper_bgcolor='#141f30', plot_bgcolor='#141f30', font={'family':'Arial, sans-serif', 'color':'#dce4ee'}, margin={'l':65,'r':25,'t':65,'b':55}, height=370, hovermode='x unified', legend={'orientation':'h', 'y':1.12}, yaxis={'rangemode':'tozero'}, xaxis={'showgrid':False})
        result.append(json.loads(fig.to_json()))
    return result


@app.get('/')
def index():
    return render_template('index.html', start=DATA.date.min().strftime('%Y-%m-%d'), end=DATA.date.max().strftime('%Y-%m-%d'))


@app.get('/api/dashboard')
def dashboard():
    try:
        frame = selected()
        return jsonify(summary=summarize(frame), figures=figures(frame))
    except (ValueError, OverflowError):
        return jsonify(error='Invalid metric or date range. Use cases/deaths and dates within the snapshot.'), 400


@app.get('/export.csv')
def export():
    try:
        frame = selected()
        frame['date'] = frame.date.dt.strftime('%Y-%m-%d')
        return Response(frame.to_csv(index=False), mimetype='text/csv', headers={'Content-Disposition':'attachment; filename=covid-19-filtered.csv'})
    except (ValueError, OverflowError):
        return jsonify(error='Invalid or empty date range.'), 400


@app.get('/plotly.js')
def plotly_js():
    return Response(get_plotlyjs(), mimetype='application/javascript', headers={'Cache-Control':'public, max-age=86400'})


@app.get('/health')
def health():
    return jsonify(status='ok', observations=len(DATA))


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
