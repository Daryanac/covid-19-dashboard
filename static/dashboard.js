const form = document.querySelector('#filters');
const status = document.querySelector('#status');
const number = new Intl.NumberFormat('en-US', {maximumFractionDigits: 0});
async function update() {
  const button = document.querySelector('#apply');
  button.disabled = true;
  status.textContent = 'Loading historical data…';
  const params = new URLSearchParams({start: form.querySelector('#start').value, end: form.querySelector('#end').value, metric: form.querySelector('#metric').value});
  try {
    const response = await fetch(`/api/dashboard?${params}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    if (!window.Plotly) throw new Error('Charts could not load. Please reload this page.');
    const s = data.summary;
    document.querySelector('#cases').textContent = number.format(s.cumulative_cases);
    document.querySelector('#deaths').textContent = number.format(s.cumulative_deaths);
    document.querySelector('#new').textContent = number.format(s.net_new_cases);
    document.querySelector('#peak').textContent = s.case_peak ? number.format(s.case_peak.value) : 'N/A';
    document.querySelector('#peakdate').textContent = s.case_peak ? `On ${s.case_peak.date}` : 'Not enough preceding daily observations';
    await Promise.all(['daily', 'cumulative', 'monthly'].map((id, i) => Plotly.react(id, data.figures[i].data, data.figures[i].layout, {responsive: true, displaylogo: false})));
    document.querySelector('#export').href = `/export.csv?${params}`;
    status.textContent = `${s.start} → ${s.end} · ${number.format(s.observations)} observations · ${s.correction_days} correction days${s.unknown_baseline_days ? ' · First daily change excluded: unknown baseline' : ''}`;
  } catch (error) {
    status.textContent = error.message || 'Unable to load the dashboard. Please try again.';
  } finally { button.disabled = false; }
}
form.addEventListener('submit', event => { event.preventDefault(); update(); });
update();
