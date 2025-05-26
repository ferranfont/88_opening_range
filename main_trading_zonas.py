# ANDREA UNGER TRADING SYSTEM BREAK OUT OPENING RANGE (GRID DE RETRACEMENTS)
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import order_managment_zonas as omz
import chart_volume as chart
import estadisticas as st
import find_high_volume_candles as hv
import webbrowser
import os

now_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
load_dotenv()

# ===================== CONFIGURACIÓN DE GRID =====================
last_100_dates_file = os.path.join('outputs', 'unique_dates.txt')
# Puedes ampliar retracts si quieres hacer el grid completo
#retracts = [0, 0.001, 0.002, 0.003, 0.004, 0.005, 0.006, 0.007, 0.008, 0.009, 0.01, 0.05, 0.1, 0.5]
retracts = [0]

# ===================== LIMPIEZA DE TRACKING =====================
tracking_file = 'outputs/tracking_record.csv'
if os.path.exists(tracking_file):
    os.remove(tracking_file)

# ===================== LECTURA DE FECHAS =====================
dates = []
if os.path.exists(last_100_dates_file):
    with open(last_100_dates_file, 'r') as f:
        dates = [line.strip() for line in f.readlines()]
    print(f"✅ Loaded {len(dates)} dates from {last_100_dates_file}")

# ==== FILTRO PARA FECHAS POSTERIORES A 2025-04-15 ====
min_date = datetime.strptime('2024-01-15', '%Y-%m-%d').date()
dates = [d for d in dates if d >= '2024-01-15']

dates = ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19', '2024-01-22', '2024-01-23', '2024-01-24', '2024-01-25', '2024-01-26' ]
#dates = ['2024-01-25']
print(f"✅ Filtradas {len(dates)} fechas")

# ===================== BUCLE PRINCIPAL DE GRID =====================
for retracement in retracts:
    print(f"\n=== PROBANDO RETRACEMENT: {retracement} ===")
    for fecha in dates:
        print(f"\n📅 ANALIZANDO EL DIA: {fecha} | Retracement: {retracement}")
        # Inicialización de variables
        hora = "16:30:00"
        lookback_min = 60
        entry_shift = 0
        START_DATE = pd.Timestamp(fecha, tz='Europe/Madrid')
        END_DATE = pd.Timestamp(fecha, tz='Europe/Madrid')
        END_TIME = pd.Timestamp(f'{fecha} {hora}', tz='Europe/Madrid')
        START_TIME = END_TIME - pd.Timedelta(minutes=lookback_min)
        too_late_patito_negro = "21:55:00"
        too_late_brake_fractal_pauta_plana = "18:30:00"
        limit_time = END_TIME + pd.Timedelta(minutes=90)   #Hora máxima para admitir traders en ese dia
        strength_target =5
        too_late_patito_negro = pd.Timestamp(f'{fecha} {too_late_patito_negro}', tz='Europe/Madrid')
        TRADING_WINDOW_TIME = (pd.Timestamp(f'{fecha} {hora}', tz='Europe/Madrid'), pd.Timestamp(f'{fecha} {too_late_patito_negro}', tz='Europe/Madrid'))

        # ===================== DATOS =====================
        directorio = '../DATA'
        nombre_fichero = 'ES_2015_2024_5min_timeframe.csv'
        ruta_completa = os.path.join(directorio, nombre_fichero)
        df = pd.read_csv(ruta_completa)

        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], utc=True)
            df.set_index('Date', inplace=True)
        df.index = df.index.tz_convert('Europe/Madrid')
        df_subset = df[(df.index.date >= START_DATE.date()) & (df.index.date <= END_DATE.date())]
        fecha_trading_sp = df_subset['Close'].iloc[-1]

        # ===================== RANGOS =====================
        window_df = df[(df.index >= START_TIME) & (df.index <= END_TIME)]
        if not window_df.empty:
            y0_value = window_df['Low'].min()
            y1_value = window_df['High'].max()
        opening_range = y1_value - y0_value

        y0_subvalue = window_df['Close'].min()
        y1_subvalue = window_df['Close'].max()
        opening_range_subvalue = y1_subvalue - y0_subvalue

        # ===================== DATOS POST-APERTURA =====================
        after_open_df = df_subset[df_subset.index >= END_TIME]

        # ===================== DETECCIÓN BREAKOUT/BREAKDOWN =====================
        first_breakout_time = None
        first_breakout_price = None
        first_breakout_bool = False

        first_breakdown_time = None
        first_breakdown_price = None
        first_breakdown_bool = False

        breakout_rows = after_open_df[after_open_df['Close'] > y1_subvalue]
        if not breakout_rows.empty:
            first_breakout_time = breakout_rows.index[0]
            first_breakout_price = breakout_rows.iloc[0]['Close']
            first_breakout_bool = True

        breakdown_rows = after_open_df[after_open_df['Close'] < y0_subvalue]
        if not breakdown_rows.empty:
            first_breakdown_time = breakdown_rows.index[0]
            first_breakdown_price = breakdown_rows.iloc[0]['Close']
            first_breakdown_bool = True

        # ===================== ESTADÍSTICAS (OPCIONAL) =====================
        resultado = st.estadisticas(
            after_open_df=after_open_df,
            y0_value=y0_value,
            y1_value=y1_value,
            y0_subvalue=y0_subvalue,
            y1_subvalue=y1_subvalue,
            first_breakout_time=first_breakout_time,
            first_breakout_price=first_breakout_price,
            first_breakdown_time=first_breakdown_time,
            first_breakdown_price=first_breakdown_price,
            first_breakout_bool=first_breakout_bool,
            first_breakdown_bool=first_breakdown_bool,
            fecha=fecha,
            fecha_trading_sp=fecha_trading_sp
        )
        df_stadisticas = pd.DataFrame([resultado])
        print(df_stadisticas.T)

        # ===================== HIGH VOLUME CANDLES (OPCIONAL) =====================
        df_high_volumen_candles = hv.df_high_volumen_candles(
            df_subset,
            TRADING_WINDOW_TIME,
            y0_value,
            y1_value,
            n=2,
            factor=1
        )
        df_high_volumen_candles = df_high_volumen_candles[df_high_volumen_candles['Volumen_Alto']]

        # ===================== ORDER MANAGMENT Y TRACKING =====================
        df_trade_result = omz.order_management_zonas(
            after_open_df=after_open_df,
            limit_time=limit_time,
            y0_value=y0_value,
            y1_value=y1_value,
            y0_subvalue=y0_subvalue,
            y1_subvalue=y1_subvalue,
            opening_range=opening_range,
            retracement=retracement,
            strength_target=strength_target
        )


        print("\n📌 Señales generadas por Order Management ZONAS:")
        print(df_trade_result.T)


        #df_trade_result = pd.DataFrame([trade_result])
        #print("\n📌 Señales generadas por Order Management:")
        #print(df_trade_result.T)

        # GRAFICACIÓN SOLO PARA EL PRIMER RETRACEMENT (por eficiencia)
        
        if retracement == retracts[0]:     # MODIFICAR ESTE PARÁMETRO PARA CREAT GRAFICOS PARA TODOS LOS RETROCESOS
            titulo = f"Chart_{fecha}_retro_{retracement}"
            entry_type = df_trade_result.iloc[0]['entry_type'] if 'entry_type' in df_trade_result.columns else None
        chart.graficar_precio(
            df_subset,
            limit_time,
            too_late_patito_negro,
            titulo,
            START_TIME,
            END_TIME,
            y0_value,
            y1_value,
            y0_subvalue,
            y1_subvalue,
            first_breakout_time,
            first_breakout_price,
            first_breakdown_time,
            first_breakdown_price,
            df_high_volumen_candles,
            df_trade_result
        )

            
# ===================== RESUMEN Y PUBLICACIÓN HTML =====================
tracking_file = 'outputs/tracking_record.csv'
df = pd.read_csv(tracking_file)

# Limpia tipos numéricos
for col in ['profit_points', 'profit_usd', 'retracement_level']:
    df[col] = pd.to_numeric(df[col], errors='coerce')
df = df[df['entry_type'].notnull() & df['retracement_level'].notnull()]

# --- TABLA 1: Por entry_type y retracement_level ---
grouped = df.groupby(['entry_type', 'retracement_level'])
summary = grouped.agg(
    total_trades=('profit_points', 'count'),
    sum_profit_points=('profit_points', lambda x: int(round(x.sum()))),
    sum_profit_usd=('profit_usd', lambda x: round(x.sum(), 2)),
    avg_profit_points=('profit_points', lambda x: round(x.mean(), 2)),
    avg_profit_usd=('profit_usd', lambda x: round(x.mean(), 2))
).reset_index()
summary = summary.sort_values(['entry_type', 'retracement_level']).reset_index(drop=True)

# --- TABLA 2: Sólo por retracement_level ---
grouped2 = df.groupby('retracement_level')
summary2 = grouped2.agg(
    total_trades=('profit_points', 'count'),
    sum_profit_points=('profit_points', lambda x: int(round(x.sum()))),
    sum_profit_usd=('profit_usd', lambda x: round(x.sum(), 2)),
    avg_profit_points=('profit_points', lambda x: round(x.mean(), 2)),
    avg_profit_usd=('profit_usd', lambda x: round(x.mean(), 2))
).reset_index()
summary2 = summary2.sort_values('retracement_level').reset_index(drop=True)

# GUARDA summary2 PARA EL HISTOGRAMA
summary2_csv = 'outputs/summary_by_retracement_only.csv'
summary2.to_csv(summary2_csv, index=False)
print(f"\n✅ summary2 guardado como CSV en {summary2_csv}")


# Formatea decimales SOLO para HTML (no afecta los cálculos)
summary['retracement_level'] = summary['retracement_level'].map('{:.3f}'.format)
summary2['retracement_level'] = summary2['retracement_level'].map('{:.3f}'.format)

for col in ['avg_profit_points', 'avg_profit_usd', 'sum_profit_usd']:
    if col in summary:
        summary[col] = summary[col].map(lambda x: '{:.2f}'.format(x) if pd.notnull(x) else '')
    if col in summary2:
        summary2[col] = summary2[col].map(lambda x: '{:.2f}'.format(x) if pd.notnull(x) else '')
if 'sum_profit_points' in summary:
    summary['sum_profit_points'] = summary['sum_profit_points'].map(lambda x: str(int(round(float(x)))) if pd.notnull(x) else '')
if 'sum_profit_points' in summary2:
    summary2['sum_profit_points'] = summary2['sum_profit_points'].map(lambda x: str(int(round(float(x)))) if pd.notnull(x) else '')

html_output = f"""
<html>
<head>
    <meta charset="UTF-8">
    <title>Resumen Backtest Retracement Level</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: #fff; }}
        h2 {{ margin-top: 40px; color: #133059; }}
        table {{ border-collapse: collapse; width: 90%; margin: 0 auto 30px auto; font-size: 1.15em; }}
        th, td {{ border: 1px solid #d5dbe0; padding: 8px 12px; text-align: center; }}
        th {{ background: #edf2fa; color: #13437c; font-size: 1.08em; }}
        tr:nth-child(even) {{ background: #f8fafc; }}
        tr:hover {{ background: #d8ecf7; }}
        .title {{ margin: 30px auto 10px auto; text-align: left; width: 90%; color: #173159; }}
    </style>
</head>
<body>
    <h2 class="title">Resumen por Tipo de Entrada y Retracement Level</h2>
    {summary.to_html(index=False, escape=False)}
    <h2 class="title">Resumen SOLO por Retracement Level</h2>
    {summary2.to_html(index=False, escape=False)}
</body>
</html>
"""

os.makedirs('charts', exist_ok=True)
output_file = os.path.abspath('charts/resumen_backtest_retracement.html')
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_output)

# Abre el HTML generado en el navegador por defecto
webbrowser.open('file://' + output_file)

print(f"\n✅ Resumen HTML guardado en {output_file} y abierto en tu navegador.")


# ============= HISTOGRAMA DE SUM PROFIT POINTS POR RETRACEMENT LEVEL =============
import plotly.graph_objects as go

summary_csv = 'outputs/summary_by_retracement_only.csv'
if os.path.exists(summary_csv):
    df_hist = pd.read_csv(summary_csv)
    df_hist.columns = [col.strip() for col in df_hist.columns]
    for col in ['retracement_level', 'sum_profit_points']:
        if col in df_hist.columns:
            df_hist[col] = pd.to_numeric(df_hist[col], errors='coerce')
    df_hist = df_hist.sort_values('retracement_level')

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_hist['retracement_level'],
        y=df_hist['sum_profit_points'],
        text=df_hist['sum_profit_points'],
        textposition='outside',
        marker_color='royalblue'
    ))
    fig.update_layout(
        title="Histograma: Retracement Level vs. Sum Profit Points",
        xaxis_title="Retracement Level",
        yaxis_title="Sum Profit Points",
        template="plotly_white",
        width=900,
        height=450
    )

    hist_output = os.path.abspath('charts/histograma_sum_profit_points.html')
    fig.write_html(hist_output, auto_open=False)
    print(f"\n✅ Histograma guardado en {hist_output}")
    webbrowser.open('file://' + hist_output)
else:
    print(f"\n❌ No se encontró el archivo {summary_csv} para crear el histograma.")