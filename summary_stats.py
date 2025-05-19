import os
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import webbrowser

# === ARCHIVOS ===
summary_file = 'outputs/summary_stats.csv'

# === LEER SUMMARY ===
summary_df = pd.read_csv(summary_file, parse_dates=['Fecha'])
summary_df.set_index('Fecha', inplace=True)
summary_df.sort_index(inplace=True)

# === CONVERTIR AWARE A tz-naive (yfinance usa naive) ===
summary_df.index = summary_df.index.tz_localize(None)

# === CALCULAR PROFIT ACUMULADO ===
usd_por_punto = 50
summary_df['target_profit_outside_range'] = summary_df['target_profit_outside_range'].astype(str).str.strip().map({'True': True, 'False': False})
summary_df['stop_out_outside_range'] = summary_df['stop_out_outside_range'].astype(str).str.strip().map({'True': True, 'False': False})
summary_df['target_profit_mfe_time'] = pd.to_datetime(summary_df['target_profit_mfe_time'], errors='coerce')
summary_df['stop_out_time'] = pd.to_datetime(summary_df['stop_out_time'], errors='coerce')

profits = []
points_used = []

for idx, row in summary_df.iterrows():
    tp = row['target_profit_outside_range']
    so = row['stop_out_outside_range']
    tp_time = row['target_profit_mfe_time']
    so_time = row['stop_out_time']

    if tp and not so:
        points = row['profit_points_outside_range']
    elif so and not tp:
        points = -row['lost_outside_range']
    elif tp and so:
        if pd.notna(tp_time) and pd.notna(so_time):
            points = row['profit_points_outside_range'] if tp_time < so_time else -row['lost_outside_range']
        elif pd.notna(tp_time):
            points = row['profit_points_outside_range']
        elif pd.notna(so_time):
            points = -row['lost_outside_range']
        else:
            points = 0
    else:
        points = 0

    points_used.append(points)
    profits.append(points * usd_por_punto)

summary_df['Profit_points_used'] = points_used
summary_df['Profit_$'] = profits
summary_df['Cumulative_Profit_$'] = summary_df['Profit_$'].cumsum()

# === RANGO DE FECHAS PARA YFINANCE ===
start_date = summary_df.index.min().strftime('%Y-%m-%d')
end_date = (summary_df.index.max() + pd.Timedelta(days=1)).strftime('%Y-%m-%d')

# === DESCARGA DE PRECIO DEL S&P 500 ===
sp500 = yf.download("^GSPC", start=start_date, end=end_date)  # usa SPX (^GSPC) o SPY
sp500_daily = sp500['Close'].copy()
sp500_daily.index = pd.to_datetime(sp500_daily.index)
sp500_daily = sp500_daily[summary_df.index.min():summary_df.index.max()]

# === GRAFICAR ===
fig = make_subplots(
    rows=2,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.05,
    row_heights=[0.4, 0.6],
    subplot_titles=("Evolución del S&P 500 (línea)", "Cumulative Profit ($, área)")
)

# === SP500 LINE ===
fig.add_trace(go.Scatter(
    x=sp500_daily.index,
    y=sp500_daily,
    mode='lines',
    line=dict(color='royalblue'),
    name='S&P 500'
), row=1, col=1)

# === PROFIT ACUMULADO COMO ÁREA ===
color_fill = 'green' if summary_df['Cumulative_Profit_$'].iloc[-1] >= 0 else 'red'
fig.add_trace(go.Scatter(
    x=summary_df.index,
    y=summary_df['Cumulative_Profit_$'],
    mode='lines',
    fill='tozeroy',
    line=dict(color=color_fill),
    name='Profit $'
), row=2, col=1)

# === ESTILO ===
fig.update_layout(
    title="S&P 500 vs. Profit Acumulado ($)",
    height=700,
    width=1200,
    plot_bgcolor='white',
    paper_bgcolor='white',
    font=dict(size=12, color="black"),
    margin=dict(l=40, r=40, t=60, b=40),
    showlegend=False
)

fig.update_xaxes(title_text="Fecha", row=2, col=1)
fig.update_yaxes(title_text="Precio S&P 500", row=1, col=1)
fig.update_yaxes(title_text="Profit Acumulado ($)", row=2, col=1)

# === EXPORTAR Y ABRIR ===
output_file = "charts/Summary_vs_SP500_YF.html"
os.makedirs("charts", exist_ok=True)
fig.write_html(output_file, auto_open=False)
print(f"📁 Gráfico guardado en: {output_file}")
webbrowser.open('file://' + os.path.realpath(output_file))
