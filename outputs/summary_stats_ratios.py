import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import webbrowser

# === ARCHIVOS ===
summary_file = 'outputs/summary_stats.csv'
summary_df = pd.read_csv(summary_file)

# === LIMPIEZA Y PREPROCESADO ===
summary_df.columns = summary_df.columns.str.strip()
possible_date_cols = [col for col in summary_df.columns if 'fecha' in col.lower() or 'date' in col.lower()]
if not possible_date_cols:
    raise KeyError("❌ No se encontró ninguna columna de fecha.")
date_col = possible_date_cols[0]
summary_df[date_col] = pd.to_datetime(summary_df[date_col], errors='coerce')
summary_df = summary_df.dropna(subset=[date_col])
summary_df.set_index(date_col, inplace=True)
summary_df.index = summary_df.index.tz_localize(None)
summary_df.sort_index(inplace=True)

# === FORMATO Y CONVERSIÓN ===
usd_por_punto = 50
summary_df['target_profit_outside_range'] = summary_df['target_profit_outside_range'].astype(str).str.strip().map({'True': True, 'False': False})
summary_df['stop_out_outside_range'] = summary_df['stop_out_outside_range'].astype(str).str.strip().map({'True': True, 'False': False})
summary_df['target_profit_mfe_time'] = pd.to_datetime(summary_df['target_profit_mfe_time'], errors='coerce', utc=True)
summary_df['stop_out_time'] = pd.to_datetime(summary_df['stop_out_time'], errors='coerce', utc=True)
summary_df['profit_points_outside_range'] = pd.to_numeric(summary_df['profit_points_outside_range'], errors='coerce')
summary_df['lost_outside_range'] = pd.to_numeric(summary_df['lost_outside_range'], errors='coerce')

# === CÁLCULO DE BENEFICIO ===
profits = []
points_used = []
wins = 0
losses = 0

for _, row in summary_df.iterrows():
    tp, so = row['target_profit_outside_range'], row['stop_out_outside_range']
    tp_time, so_time = row['target_profit_mfe_time'], row['stop_out_time']

    if tp and not so:
        points = row['profit_points_outside_range']
        wins += 1
    elif so and not tp:
        points = -row['lost_outside_range']
        losses += 1
    elif tp and so:
        if pd.notna(tp_time) and pd.notna(so_time):
            if tp_time < so_time:
                points = row['profit_points_outside_range']
                wins += 1
            else:
                points = -row['lost_outside_range']
                losses += 1
        elif pd.notna(tp_time):
            points = row['profit_points_outside_range']
            wins += 1
        elif pd.notna(so_time):
            points = -row['lost_outside_range']
            losses += 1
        else:
            points = 0
    else:
        points = 0

    points_used.append(points)
    profits.append(points * usd_por_punto)

summary_df['Profit_points_used'] = points_used
summary_df['Profit_$'] = profits
summary_df['Cumulative_Profit_$'] = summary_df['Profit_$'].cumsum()

# === CALCULO DE RATIOS ===
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

# === TABLA BONITA CON PLOTLY ===
fig_table = go.Figure(data=[go.Table(
    header=dict(values=["📊 Métrica", "🔢 Valor"],
                fill_color='paleturquoise',
                align='left'),
    cells=dict(values=[
        ['Total Trades', 'Stop Out True', 'Stop Out False', 'Stop Out True (%)', 'Stop Out False (%)',
         'Average Take Profit (Points)', 'Average Lost (Points)', 'Profit Factor',
         'Sharpe Ratio', 'Sortino Ratio', 'Win Rate (%)', 'Loss Rate (%)'],
        [total, stop_out_true, stop_out_false, pct_stop_out_true, pct_stop_out_false,
         round(avg_tp_points, 2), round(avg_lost_points, 2), round(profit_factor, 2),
         round(sharpe_ratio, 2), round(sortino_ratio, 2), win_rate, loss_rate]
    ],
    fill_color='lavender',
    align='left'))
])

fig_table.update_layout(
    title='📋 Trading Performance Metrics',
    width=900,
    height=600
)

output_table = "charts/Table_Trading_Metrics.html"
os.makedirs("charts", exist_ok=True)
fig_table.write_html(output_table, auto_open=True)
print(f"📁 Tabla de métricas guardada en: {output_table}")

# === IMPRIMIR EN TERMINAL TAMBIÉN ===
print("\n📊 TRADING PERFORMANCE METRICS:")
print(f"Total Trades:                   {total}")
print(f"Stop:                           {stop_out_true} ({pct_stop_out_true}%)")
print(f"Target Profit:                  {stop_out_false} ({pct_stop_out_false}%)")
print(f"Win Rate:                       {win_rate}%")
print(f"Loss Rate:                      {loss_rate}%")
print(f"Average Take Profit (points):   {round(avg_tp_points, 2)}")
print(f"Average Lost (oiubts):          {round(avg_lost_points, 2)}")
print(f"Profit Factor:                  {round(profit_factor, 2)}")
print(f"Sharpe Ratio:                   {round(sharpe_ratio, 2)}")
print(f"Sortino Ratio:                  {round(sortino_ratio, 2)}")


