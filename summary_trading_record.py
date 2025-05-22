import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import webbrowser

# === CONFIGURACIÓN Y LECTURA ===
tracking_file = 'outputs/tracking_record.csv'
if not os.path.exists(tracking_file):
    raise FileNotFoundError(f"No se encuentra el archivo {tracking_file}")

df = pd.read_csv(tracking_file)

# Convertir columnas relevantes
if 'activation_time' in df.columns:
    df['activation_time'] = pd.to_datetime(df['activation_time'], errors='coerce')
if 'exit_time' in df.columns:
    df['exit_time'] = pd.to_datetime(df['exit_time'], errors='coerce')

df = df.sort_values(by='activation_time')
df = df.reset_index(drop=True)

# Filtrar solo trades reales
real_trades = df[df['num_positions'] > 0].copy()

# === PROFIT ACUMULADO ===
real_trades['Profit_$'] = pd.to_numeric(real_trades['profit_usd'], errors='coerce').fillna(0)
real_trades['Cumulative_Profit_$'] = real_trades['Profit_$'].cumsum()

# === AREA CHART: PROFIT ACUMULADO ===
fig = go.Figure()

# Área verde para profit positivo, roja para drawdown (cumulative < 0)
cumulative_profit = real_trades['Cumulative_Profit_$']
x = real_trades['activation_time']

# Verde encima de 0
fig.add_trace(go.Scatter(
    x=x, y=np.maximum(cumulative_profit, 0),
    fill='tozeroy', mode='lines',
    line=dict(color='green'), name='Profit Acumulado ($)', opacity=0.7
))
# Rojo debajo de 0
fig.add_trace(go.Scatter(
    x=x, y=np.minimum(cumulative_profit, 0),
    fill='tozeroy', mode='lines',
    line=dict(color='red'), name='Drawdown', opacity=0.7
))
fig.update_layout(
    title="📈 Cumulative Profit ($) - Andrea Unger System",
    xaxis_title="Fecha",
    yaxis_title="Profit Acumulado ($)",
    width=1300, height=600,
    template='plotly_white',
    legend=dict(x=0.01, y=0.99, bordercolor="Black", borderwidth=1)
)

charts_dir = "charts"
os.makedirs(charts_dir, exist_ok=True)
area_path = os.path.join(charts_dir, "Chart_Cumulative_Profit.html")
fig.write_html(area_path, auto_open=False)
print(f"✅ Chart saved: {area_path}")

# === MÉTRICAS CLAVE ===
total_trades = len(real_trades)
total_longs = (real_trades['entry_type'] == 'Long').sum()
total_shorts = (real_trades['entry_type'] == 'Short').sum()
num_win = (real_trades['Profit_$'] > 0).sum()
num_loss = (real_trades['Profit_$'] < 0).sum()
num_be = (real_trades['Profit_$'] == 0).sum()
win_rate = 100 * num_win / total_trades if total_trades else 0
loss_rate = 100 * num_loss / total_trades if total_trades else 0

total_profit = real_trades['Profit_$'].sum()
profit_factor = (
    -real_trades.loc[real_trades['Profit_$'] > 0, 'Profit_$'].sum() /
    real_trades.loc[real_trades['Profit_$'] < 0, 'Profit_$'].sum()
    if real_trades['Profit_$'].lt(0).any() else np.nan
)
avg_win = real_trades.loc[real_trades['Profit_$'] > 0, 'Profit_$'].mean()
avg_loss = real_trades.loc[real_trades['Profit_$'] < 0, 'Profit_$'].mean()
expectancy = real_trades['Profit_$'].mean()
win_loss_ratio = avg_win / abs(avg_loss) if avg_loss != 0 else np.nan

# Sharpe y Sortino
returns = real_trades['Profit_$']
sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() != 0 else np.nan
negative_returns = returns[returns < 0]
sortino_ratio = returns.mean() / negative_returns.std() * np.sqrt(252) if negative_returns.std() != 0 else np.nan

# Máximo drawdown absoluto
cumulative = real_trades['Cumulative_Profit_$']
roll_max = cumulative.cummax()
drawdown = cumulative - roll_max
max_drawdown = drawdown.min()

# === TABLA DE RATIOS ===
metric_names = [
    "Total Trades", "Total Long", "Total Short",
    "Win Trades", "Loss Trades", "Win Rate (%)", "Loss Rate (%)",
    "Profit Factor", "Expectancy ($)", "Average Win ($)", "Average Loss ($)",
    "Win/Loss Ratio", "Total Profit ($)",
    "Sharpe Ratio", "Sortino Ratio", "Max Drawdown ($)"
]
metric_values = [
    total_trades, total_longs, total_shorts,
    num_win, num_loss, round(win_rate,2), round(loss_rate,2),
    round(profit_factor,2) if not np.isnan(profit_factor) else "--",
    round(expectancy,2), round(avg_win,2), round(avg_loss,2),
    round(win_loss_ratio,2) if not np.isnan(win_loss_ratio) else "--",
    round(total_profit,2),
    round(sharpe_ratio,2) if not np.isnan(sharpe_ratio) else "--",
    round(sortino_ratio,2) if not np.isnan(sortino_ratio) else "--",
    round(max_drawdown,2)
]

fig_table = go.Figure(data=[go.Table(
    header=dict(values=["Métrica", "Valor"], fill_color='paleturquoise', align='left'),
    cells=dict(values=[metric_names, metric_values], fill_color='lavender', align='left'))
])
fig_table.update_layout(title='📋 Trading Metrics (Andrea Unger System)', width=900, height=650)
table_path = os.path.join(charts_dir, "Table_Trading_Metrics.html")
fig_table.write_html(table_path, auto_open=False)
print(f"✅ Table saved: {table_path}")

# === ABRIR EN NAVEGADOR ===
webbrowser.open('file://' + os.path.realpath(area_path))
webbrowser.open('file://' + os.path.realpath(table_path))
