import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import webbrowser

# === CONFIGURACIÓN Y LECTURA ===
tracking_file = 'outputs/tracking_record.csv'
df = pd.read_csv(tracking_file, on_bad_lines='skip')
print(f"Columnas detectadas: {df.columns.tolist()}")
print(df.head())

# Limpieza y conversión de columnas
df['num_positions'] = pd.to_numeric(df['num_positions'], errors='coerce').fillna(0).astype(int)
df['activation_time'] = pd.to_datetime(df['entry_time'], errors='coerce', utc=True)
df['exit_time'] = pd.to_datetime(df['exit_time'], errors='coerce', utc=True)

# Ordenar por fecha de activación
df = df.sort_values(by='activation_time').reset_index(drop=True)

# === FILTRAR TRADES REALES ===
trades = df[df['num_positions'] > 0].copy()
print(f"✅ Trades reales detectados: {len(trades)}")

# PROFIT ACUMULADO
trades['Profit_$'] = pd.to_numeric(trades['profit_usd'], errors='coerce').fillna(0)
trades['Cumulative_Profit_$'] = trades['Profit_$'].cumsum()

# GRÁFICO DE PROFIT ACUMULADO: ÁREA VERDE SI >0, ROJA SI <0 (sin leyenda)
x = trades['activation_time']
y = trades['Cumulative_Profit_$']
y_pos = y.clip(lower=0)
y_neg = y.clip(upper=0)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=x, y=y_pos,
    mode='lines', line=dict(color='green'),
    fill='tozeroy', fillcolor='rgba(0,200,0,0.22)',
    showlegend=False
))
fig.add_trace(go.Scatter(
    x=x, y=y_neg,
    mode='lines', line=dict(color='red', width=1),
    fill='tozeroy', fillcolor='rgba(200,0,0,0.20)',
    showlegend=False
))
fig.add_trace(go.Scatter(
    x=x, y=y,
    mode='lines', line=dict(color='black', width=1, dash='dot'),
    opacity=0.7,
    showlegend=False
))

fig.update_layout(
    title="Cumulative Profit ($) - Andrea Unger Zonas System",
    xaxis_title="Fecha",
    yaxis_title="Profit Acumulado ($)",
    width=1300, height=600,
    template='plotly_white',
    showlegend=False
)

charts_dir = "charts"
os.makedirs(charts_dir, exist_ok=True)
area_path = os.path.join(charts_dir, "Chart_Cumulative_Profit.html")
fig.write_html(area_path, auto_open=False)
print(f"✅ Chart saved: {area_path}")

# === MÉTRICAS CLAVE ===
total_trades = len(trades)
total_longs = (trades['entry_type'].str.strip() == 'Long').sum()
total_shorts = (trades['entry_type'].str.strip() == 'Short').sum()
num_win = (trades['Profit_$'] > 0).sum()
num_loss = (trades['Profit_$'] < 0).sum()
win_rate = 100 * num_win / total_trades if total_trades else 0
loss_rate = 100 * num_loss / total_trades if total_trades else 0

total_profit = trades['Profit_$'].sum()
profit_factor = (
    trades.loc[trades['Profit_$'] > 0, 'Profit_$'].sum() /
    abs(trades.loc[trades['Profit_$'] < 0, 'Profit_$'].sum())
    if trades['Profit_$'].lt(0).any() else np.nan
)
avg_win = trades.loc[trades['Profit_$'] > 0, 'Profit_$'].mean()
avg_loss = trades.loc[trades['Profit_$'] < 0, 'Profit_$'].mean()
expectancy = trades['Profit_$'].mean()
win_loss_ratio = avg_win / abs(avg_loss) if avg_loss != 0 else np.nan

returns = trades['Profit_$']
sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() != 0 else np.nan
negative_returns = returns[returns < 0]
sortino_ratio = returns.mean() / negative_returns.std() * np.sqrt(252) if negative_returns.std() != 0 else np.nan

cumulative = trades['Cumulative_Profit_$']
roll_max = cumulative.cummax()
drawdown = cumulative - roll_max
max_drawdown = drawdown.min()

# === TABLA DE MÉTRICAS ===
metric_names = [
    "Total Trades", "Total Long", "Total Short",
    "Win Trades", "Loss Trades", "Win Rate (%)", "Loss Rate (%)",
    "Profit Factor", "Expectancy ($)", "Average Win ($)", "Average Loss ($)",
    "Win/Loss Ratio", "Total Profit ($)",
    "Sharpe Ratio", "Sortino Ratio", "Max Drawdown ($)"
]
metric_values = [
    total_trades, total_longs, total_shorts,
    num_win, num_loss, round(win_rate, 2), round(loss_rate, 2),
    round(profit_factor, 2) if not np.isnan(profit_factor) else "--",
    round(expectancy, 2),
    round(avg_win, 2) if not np.isnan(avg_win) else "--",
    round(avg_loss, 2) if not np.isnan(avg_loss) else "--",
    round(win_loss_ratio, 2) if not np.isnan(win_loss_ratio) else "--",
    round(total_profit, 2),
    round(sharpe_ratio, 2) if not np.isnan(sharpe_ratio) else "--",
    round(sortino_ratio, 2) if not np.isnan(sortino_ratio) else "--",
    round(max_drawdown, 2)
]

fig_table = go.Figure(data=[go.Table(
    header=dict(values=["Métrica", "Valor"], fill_color='paleturquoise', align='left'),
    cells=dict(values=[metric_names, metric_values], fill_color='lavender', align='left'))
])
fig_table.update_layout(title='Trading Metrics (Andrea Unger Zonas System)', width=900, height=650)
table_path = os.path.join(charts_dir, "Table_Trading_Metrics.html")
fig_table.write_html(table_path, auto_open=False)
print(f"✅ Table saved: {table_path}")

# === TABLA DE DATOS (25 FILAS, SELECCIÓN) ===
trades_display = trades.copy()
trades_display['activation_time'] = trades_display['activation_time'].dt.strftime('%Y-%m-%d %H:%M')
show_cols = [
    'activation_time', 'entry_type', 'Profit_$', 'Cumulative_Profit_$',
    'entry_price', 'exit_price', 'num_positions', 'zona', 'trigger', 'output_tag'
]
for col in show_cols:
    if col not in trades_display.columns:
        trades_display[col] = ""
trades_display = trades_display[show_cols].head(25)

fig_sel = go.Figure(data=[go.Table(
    header=dict(values=list(trades_display.columns), fill_color='paleturquoise', align='left'),
    cells=dict(values=[trades_display[col] for col in trades_display.columns], fill_color='lavender', align='left'))
])
fig_sel.update_layout(title='Detalle de Trades Reales (Selección)', width=1500, height=600)
sel_table_path = os.path.join(charts_dir, "Table_Trades_Complete.html")
fig_sel.write_html(sel_table_path, auto_open=False)
print(f"✅ Tabla selección guardada: {sel_table_path}")

# === TABLA FULL (30 FILAS, TODAS LAS COLUMNAS) ===
trades_full = trades.copy()
trades_full['activation_time'] = trades_full['activation_time'].dt.strftime('%Y-%m-%d %H:%M')
trades_full['exit_time'] = trades_full['exit_time'].dt.strftime('%Y-%m-%d %H:%M')
trades_full_display = trades_full.head(30)
fig_full = go.Figure(data=[go.Table(
    header=dict(values=list(trades_full_display.columns), fill_color='paleturquoise', align='left'),
    cells=dict(values=[trades_full_display[col] for col in trades_full_display.columns], fill_color='lavender', align='left'))
])
fig_full.update_layout(title='Listado Completo de Trades (30 primeras filas)', width=2200, height=700)
full_table_path = os.path.join(charts_dir, "Table_Trades_AllColumns.html")
fig_full.write_html(full_table_path, auto_open=False)
print(f"✅ Tabla full guardada: {full_table_path}")

# ABRIR EN NAVEGADOR
webbrowser.open('file://' + os.path.realpath(area_path))
webbrowser.open('file://' + os.path.realpath(table_path))
webbrowser.open('file://' + os.path.realpath(sel_table_path))
webbrowser.open('file://' + os.path.realpath(full_table_path))

# ========== HISTOGRAMAS DE BENEFICIO POR ZONA ==========

zonas = ['Breakout', 'Breakdown', 'A', 'B', 'C']
for zona in zonas:
    trades_zona = trades[trades['zona'] == zona]
    if not trades_zona.empty:
        fig_hist = px.histogram(
            trades_zona,
            x='Profit_$',
            nbins=40,
            title=f"Histograma del Beneficio ($) - Zona {zona}",
            labels={'Profit_$': 'Beneficio ($)'},
            template='plotly_white',
            width=800,
            height=500
        )
        hist_path = os.path.join(charts_dir, f"Hist_Beneficio_Zona_{zona}.html")
        fig_hist.write_html(hist_path, auto_open=False)
        print(f"✅ Histograma zona {zona} guardado: {hist_path}")
        webbrowser.open('file://' + os.path.realpath(hist_path))
    else:
        print(f"No hay trades para la zona {zona}.")
