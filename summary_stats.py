import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import webbrowser

# === ARCHIVO ===
summary_file = 'outputs/summary_stats.csv'
summary_df = pd.read_csv(summary_file)

# === LIMPIEZA Y FORMATO ===
summary_df.columns = summary_df.columns.str.strip()
date_col = next((col for col in summary_df.columns if 'fecha' in col.lower() or 'date' in col.lower()), None)
if date_col is None:
    raise KeyError("❌ No se encontró ninguna columna de fecha.")
summary_df[date_col] = pd.to_datetime(summary_df[date_col], errors='coerce')
summary_df = summary_df.dropna(subset=[date_col])
summary_df.set_index(date_col, inplace=True)
summary_df.index = summary_df.index.tz_localize(None)
summary_df.sort_index(inplace=True)

usd_por_punto = 50
summary_df['target_profit_outside_range'] = summary_df['target_profit_outside_range'].astype(str).str.strip().map({'True': True, 'False': False})
summary_df['stop_out_outside_range'] = summary_df['stop_out_outside_range'].astype(str).str.strip().map({'True': True, 'False': False})
summary_df['target_profit_mfe_time'] = pd.to_datetime(summary_df['target_profit_mfe_time'], errors='coerce', utc=True)
summary_df['stop_out_time'] = pd.to_datetime(summary_df['stop_out_time'], errors='coerce', utc=True)
summary_df['profit_points_outside_range'] = pd.to_numeric(summary_df['profit_points_outside_range'], errors='coerce')
summary_df['lost_outside_range'] = pd.to_numeric(summary_df['lost_outside_range'], errors='coerce')

# === CALCULO DE PROFIT ===
profits, points_used = [], []
wins = losses = 0
for _, row in summary_df.iterrows():
    tp, so = row['target_profit_outside_range'], row['stop_out_outside_range']
    tp_time, so_time = row['target_profit_mfe_time'], row['stop_out_time']
    if tp and not so:
        points = row['profit_points_outside_range']; wins += 1
    elif so and not tp:
        points = -row['lost_outside_range']; losses += 1
    elif tp and so:
        if pd.notna(tp_time) and pd.notna(so_time):
            if tp_time < so_time:
                points = row['profit_points_outside_range']; wins += 1
            else:
                points = -row['lost_outside_range']; losses += 1
        elif pd.notna(tp_time):
            points = row['profit_points_outside_range']; wins += 1
        elif pd.notna(so_time):
            points = -row['lost_outside_range']; losses += 1
        else:
            points = 0
    else:
        points = 0
    points_used.append(points)
    profits.append(points * usd_por_punto)

summary_df['Profit_points_used'] = points_used
summary_df['Profit_$'] = profits
summary_df['Cumulative_Profit_$'] = summary_df['Profit_$'].cumsum()

# === DRAWDOWN ===
peak = summary_df['Cumulative_Profit_$'].cummax()
summary_df['Drawdown_%'] = ((summary_df['Cumulative_Profit_$'] - peak) / peak * 100).fillna(0)

# === RATIOS ===
total = len(summary_df)
stop_out_true = summary_df['stop_out_outside_range'].sum()
stop_out_false = total - stop_out_true
pct_stop_out_true = round(100 * stop_out_true / total, 2)
pct_stop_out_false = round(100 * stop_out_false / total, 2)
avg_tp_points = summary_df.loc[summary_df['Profit_points_used'] > 0, 'Profit_points_used'].mean()
avg_lost_points = summary_df.loc[summary_df['Profit_points_used'] < 0, 'Profit_points_used'].mean()
profit_factor = -summary_df.loc[summary_df['Profit_points_used'] > 0, 'Profit_points_used'].sum() / summary_df.loc[summary_df['Profit_points_used'] < 0, 'Profit_points_used'].sum()
returns = summary_df['Profit_$']
sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() != 0 else np.nan
negative_returns = returns[returns < 0]
sortino_ratio = returns.mean() / negative_returns.std() * np.sqrt(252) if negative_returns.std() != 0 else np.nan
win_rate = round(100 * wins / total, 2)
loss_rate = round(100 * losses / total, 2)

# === TABLA DE MÉTRICAS ===
fig_table = go.Figure(data=[go.Table(
    header=dict(values=["📊 Métrica", "🔢 Valor"], fill_color='paleturquoise', align='left'),
    cells=dict(values=[
        ['Total Trades', 'Stop Out True', 'Stop Out False', 'Stop Out True (%)', 'Stop Out False (%)',
         'Average Take Profit (Points)', 'Average Lost (Points)', 'Profit Factor',
         'Sharpe Ratio', 'Sortino Ratio', 'Win Rate (%)', 'Loss Rate (%)'],
        [total, stop_out_true, stop_out_false, pct_stop_out_true, pct_stop_out_false,
         round(avg_tp_points, 2), round(avg_lost_points, 2), round(profit_factor, 2),
         round(sharpe_ratio, 2), round(sortino_ratio, 2), win_rate, loss_rate]
    ], fill_color='lavender', align='left'))
])
fig_table.update_layout(title='📋 Trading Performance Metrics', width=900, height=600)
os.makedirs("charts", exist_ok=True)
table_path = "charts/Table_Trading_Metrics.html"
fig_table.write_html(table_path, auto_open=False)

# === CONSOLA ===
print("\n📊 TRADING PERFORMANCE METRICS:")
print(f"Total Trades:                   {total}")
print(f"Stop Out True:                  {stop_out_true} ({pct_stop_out_true}%)")
print(f"Stop Out False:                 {stop_out_false} ({pct_stop_out_false}%)")
print(f"Win Rate:                       {win_rate}%")
print(f"Loss Rate:                      {loss_rate}%")
print(f"Average Take Profit (points):   {round(avg_tp_points, 2)}")
print(f"Average Lost (points):          {round(avg_lost_points, 2)}")
print(f"Profit Factor:                  {round(profit_factor, 2)}")
print(f"Sharpe Ratio:                   {round(sharpe_ratio, 2)}")
print(f"Sortino Ratio:                  {round(sortino_ratio, 2)}")

# === MATRIZ DE CORRELACIÓN + HEATMAP ===
summary_df['MFE_desde_entrada'] = pd.to_numeric(summary_df['MFE_desde_entrada'], errors='coerce')
summary_df['MAE_desde_entrada'] = pd.to_numeric(summary_df['MAE_desde_entrada'], errors='coerce')

correlation_df = summary_df[[
    'stop_out_outside_range',
    'target_profit_outside_range',
    'rango_apertura',
    'MFE_desde_entrada',
    'MAE_desde_entrada'
]].dropna()

correlation_matrix = correlation_df.corr().round(2)
print("\n📈 MATRIZ DE CORRELACIÓN:")
print(correlation_matrix)

fig_heatmap = px.imshow(
    correlation_matrix,
    text_auto=True,
    color_continuous_scale='RdBu',
    title='🔍 Heatmap de Correlación',
    width=700, height=600
)
fig_heatmap.update_layout(margin=dict(l=50, r=50, t=60, b=50), font=dict(size=14))
heatmap_path = "charts/Heatmap_Correlacion.html"
fig_heatmap.write_html(heatmap_path, auto_open=False)

# === GRAFICO: PROFIT ACUMULADO ===
fig_profit = make_subplots(specs=[[{"secondary_y": True}]])
color_fill = 'green' if summary_df['Cumulative_Profit_$'].iloc[-1] >= 0 else 'red'
fig_profit.add_trace(go.Scatter(
    x=summary_df.index, y=summary_df['Cumulative_Profit_$'], mode='lines', fill='tozeroy',
    name='Profit Acumulado ($)', line=dict(color=color_fill)
), secondary_y=False)

if 'SP500_close' in summary_df.columns:
    fig_profit.add_trace(go.Scatter(
        x=summary_df.index, y=summary_df['SP500_close'], mode='lines',
        name='S&P 500 (Close)', line=dict(color='royalblue')
    ), secondary_y=True)

fig_profit.update_layout(
    title="📈 Profit Acumulado vs. S&P 500", height=700, width=1400,
    margin=dict(l=50, r=50, t=60, b=50), font=dict(size=13)
)
fig_profit.update_xaxes(title_text="Fecha", showline=True)
fig_profit.update_yaxes(title_text="Profit Acumulado ($)", secondary_y=False, showline=True)
fig_profit.update_yaxes(title_text="Precio S&P 500", secondary_y=True, showline=True)
profit_path = "charts/Chart_Profit_vs_SP500.html"
fig_profit.write_html(profit_path, auto_open=False)

# === GRAFICO: DRAWDOWN ===
fig_dd = go.Figure()
fig_dd.add_trace(go.Scatter(
    x=summary_df.index,
    y=summary_df['Drawdown_%'],
    mode='lines',
    fill='tozeroy',
    name='Drawdown (%)',
    line=dict(color='crimson')
))
fig_dd.update_layout(
    title="📉 Drawdown (%)", height=600, width=1400,
    plot_bgcolor='white', font=dict(size=13)
)
drawdown_path = "charts/Chart_Drawdown.html"
fig_dd.write_html(drawdown_path, auto_open=False)

# === ABRIR RESULTADOS ===
webbrowser.open('file://' + os.path.realpath(profit_path))
webbrowser.open('file://' + os.path.realpath(drawdown_path))
webbrowser.open('file://' + os.path.realpath(table_path))
webbrowser.open('file://' + os.path.realpath(heatmap_path))
