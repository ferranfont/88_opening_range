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

# === MATRIZ DE CORRELACIÓN + HEATMAP ===
summary_df['MFE_desde_entrada'] = pd.to_numeric(summary_df['MFE_desde_entrada'], errors='coerce')
summary_df['MAE_desde_entrada'] = pd.to_numeric(summary_df['MAE_desde_entrada'], errors='coerce')

correlation_df = summary_df[
    ['stop_out_outside_range', 'target_profit_outside_range', 'rango_apertura', 'MFE_desde_entrada', 'MAE_desde_entrada']
].dropna()

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

# === TABLA 1: Conteo de ocurrencias por etiqueta Pull-back relativo a Opening Range ===
pullback_counts = summary_df['Label_s/Pull-back'].value_counts().reset_index()
pullback_counts.columns = ['Etiqueta Pull-back Open Range', 'Cantidad']
etiquetas_order_open = [
    "No Pull-back", "Pull-back <5%", "Pull-back 5-10%", "Pull-back 10-20%", "Pull-back 20-25%",
    "Pull-back 25-30%", "Pull-back 30-50%", "Pull-back 50-61%", "Pull-back 61-75%",
    "Pull-back 75-100%", "Pull-back Stop-Loss", "Pull-back >100%"
]
pb_labels_order = [l for l in etiquetas_order_open if l in pullback_counts['Etiqueta Pull-back Open Range'].values]
pullback_counts_sorted = pullback_counts.set_index('Etiqueta Pull-back Open Range').loc[
    pb_labels_order
].reset_index()

fig_pullback = go.Figure(data=[go.Table(
    header=dict(values=pullback_counts.columns.tolist(), fill_color='paleturquoise', align='left'),
    cells=dict(values=[pullback_counts['Etiqueta Pull-back Open Range'], pullback_counts['Cantidad']],
               fill_color='lavender', align='left'))
])
fig_pullback.update_layout(title='📋 Conteo de Pull-back sobre Opening Range', width=600, height=400)
pullback_table_path = "charts/Table_Pullback_OpenRange.html"
fig_pullback.write_html(pullback_table_path, auto_open=False)

# === TABLA 2: Conteo de ocurrencias por etiqueta Pull-back relativo a Precio (Pull-back_PER) ===
pullback_per_counts = summary_df['Label_Pull-back_PER'].value_counts().reset_index()
pullback_per_counts.columns = ['Etiqueta Pull-back % Precio', 'Cantidad']
etiquetas_order_per = [
    "No Pull-back", "Pull-back <0.5%", "Pull-back 0.5-1%", "Pull-back 1-2%", "Pull-back 2-3%",
    "Pull-back 3-4%", "Pull-back >10%"
]
pb_per_labels_order = [l for l in etiquetas_order_per if l in pullback_per_counts['Etiqueta Pull-back % Precio'].values]
pullback_per_counts_sorted = pullback_per_counts.set_index('Etiqueta Pull-back % Precio').loc[
    pb_per_labels_order
].reset_index()

fig_pullback_per = go.Figure(data=[go.Table(
    header=dict(values=pullback_per_counts.columns.tolist(), fill_color='paleturquoise', align='left'),
    cells=dict(values=[pullback_per_counts['Etiqueta Pull-back % Precio'], pullback_per_counts['Cantidad']],
               fill_color='lavender', align='left'))
])
fig_pullback_per.update_layout(title='📋 Conteo de Pull-back sobre Precio Entrada', width=600, height=400)
pullback_per_table_path = "charts/Table_Pullback_Precio.html"
fig_pullback_per.write_html(pullback_per_table_path, auto_open=False)

# === GRAFICO DE BARRAS: CONTEO PULL-BACK SOBRE OPENING RANGE ===
fig_bar_openrange = px.bar(
    pullback_counts_sorted,
    x='Cantidad',
    y='Etiqueta Pull-back Open Range',
    orientation='h',
    title='Pull-back sobre Opening Range',
    text='Cantidad',
    color='Cantidad',
    color_continuous_scale='Blues'
)
fig_bar_openrange.update_layout(
    yaxis={'categoryorder': 'array', 'categoryarray': pb_labels_order[::-1]},
    width=900, height=550, font=dict(size=16),
    margin=dict(l=120, r=50, t=60, b=60),
    bargap=0.4
)
fig_bar_openrange.update_traces(textposition='outside', marker_line_width=1, marker_line_color='black')
bar_openrange_path = "charts/Bar_Pullback_OpenRange.html"
fig_bar_openrange.write_html(bar_openrange_path, auto_open=False)

# === GRAFICO DE BARRAS: CONTEO PULL-BACK SOBRE % PRECIO ===
fig_bar_per = px.bar(
    pullback_per_counts_sorted,
    x='Cantidad',
    y='Etiqueta Pull-back % Precio',
    orientation='h',
    title='Pull-back en % sobre Precio de Entrada',
    text='Cantidad',
    color='Cantidad',
    color_continuous_scale='Greens'
)
fig_bar_per.update_layout(
    yaxis={'categoryorder': 'array', 'categoryarray': pb_per_labels_order[::-1]},
    width=900, height=550, font=dict(size=16),
    margin=dict(l=120, r=50, t=60, b=60),
    bargap=0.4
)
fig_bar_per.update_traces(textposition='outside', marker_line_width=1, marker_line_color='black')
bar_per_path = "charts/Bar_Pullback_Precio.html"
fig_bar_per.write_html(bar_per_path, auto_open=False)

# === ANALISIS Y GRAFICO PARA LA NUEVA COLUMNA DE ZONAS (por quintiles del rango) ===
if 'Zona_Retroceso_Rango' in summary_df.columns:
    zonas_labels = [
        "No Pull-back", "Zona 20", "Zona 40", "Zona 60", "Zona 80", "Zona 100", "Zona >100"
    ]
    zonas_counts = summary_df['Zona_Retroceso_Rango'].value_counts().reset_index()
    zonas_counts.columns = ['Zona Retroceso', 'Cantidad']
    zonas_order = [l for l in zonas_labels if l in zonas_counts['Zona Retroceso'].values]
    zonas_counts_sorted = zonas_counts.set_index('Zona Retroceso').loc[zonas_order].reset_index()

    # Tabla resumen por zona
    fig_zonas = go.Figure(data=[go.Table(
        header=dict(values=zonas_counts.columns.tolist(), fill_color='paleturquoise', align='left'),
        cells=dict(values=[zonas_counts_sorted['Zona Retroceso'], zonas_counts_sorted['Cantidad']],
                   fill_color='lavender', align='left'))
    ])
    fig_zonas.update_layout(title='📋 Conteo de Retroceso por Zonas del Rango', width=600, height=400)
    zonas_table_path = "charts/Table_Pullback_Zonas.html"
    fig_zonas.write_html(zonas_table_path, auto_open=False)

    # Gráfico de barras horizontal de zonas
    fig_bar_zonas = px.bar(
        zonas_counts_sorted,
        x='Cantidad',
        y='Zona Retroceso',
        orientation='h',
        title='Pull-back por Zonas del Rango de Apertura',
        text='Cantidad',
        color='Cantidad',
        color_continuous_scale='Oranges'
    )
    fig_bar_zonas.update_layout(
        yaxis={'categoryorder': 'array', 'categoryarray': zonas_order[::-1]},
        width=900, height=550, font=dict(size=16),
        margin=dict(l=120, r=50, t=60, b=60),
        bargap=0.4
    )
    fig_bar_zonas.update_traces(textposition='outside', marker_line_width=1, marker_line_color='black')
    bar_zonas_path = "charts/Bar_Pullback_Zonas.html"
    fig_bar_zonas.write_html(bar_zonas_path, auto_open=False)

    # === TABLA INTEGRADA DE RESUMEN (por trade) ===
    tabla_integrada = summary_df[[
        'rango_apertura',               # Rango apertura (puntos)
        'retroceso_absoluto',           # Retroceso en puntos
        'Pull-back s/ Open_range',      # Retroceso en % rango apertura
        'Pull-back_PER',                # Retroceso en % sobre precio entrada
        'Zona_Retroceso_Rango',         # Zona alcanzada
        'Label_s/Pull-back',            # Etiqueta % rango apertura
        'Label_Pull-back_PER'           # Etiqueta % precio entrada
    ]].copy()

    tabla_integrada.columns = [
        "Rango Apertura (pts)",
        "Retroceso (pts)",
        "Retroceso % Rango Apertura",
        "Retroceso % Precio Entrada",
        "Zona Rango",
        "Label % Rango Apertura",
        "Label % Precio Entrada"
    ]

    # Renderizar la tabla en HTML
    fig_bigtable = go.Figure(data=[go.Table(
        header=dict(values=tabla_integrada.columns.tolist(), fill_color='paleturquoise', align='left', font=dict(size=12)),
        cells=dict(values=[tabla_integrada[c] for c in tabla_integrada.columns], fill_color='lavender', align='left', font=dict(size=11)),
    )])
    fig_bigtable.update_layout(title='Resumen Retrocesos por Trade', width=1600, height=900)
    bigtable_path = "charts/Tabla_Resumen_Retrocesos.html"
    fig_bigtable.write_html(bigtable_path, auto_open=False)

    # Abrir también los resultados de las zonas y tabla grande
    webbrowser.open('file://' + os.path.realpath(zonas_table_path))
    webbrowser.open('file://' + os.path.realpath(bar_zonas_path))
    webbrowser.open('file://' + os.path.realpath(bigtable_path))

# === ABRIR RESULTADOS SOLO UNA VEZ CADA UNO (los principales) ===
webbrowser.open('file://' + os.path.realpath(bar_openrange_path))
webbrowser.open('file://' + os.path.realpath(bar_per_path))
webbrowser.open('file://' + os.path.realpath(pullback_table_path))
webbrowser.open('file://' + os.path.realpath(pullback_per_table_path))
webbrowser.open('file://' + os.path.realpath(table_path))
webbrowser.open('file://' + os.path.realpath(profit_path))
webbrowser.open('file://' + os.path.realpath(drawdown_path))
webbrowser.open('file://' + os.path.realpath(heatmap_path))
