# ANDREA UNGER TRADING SYSTEM BREAK OUT OPENING RANGE
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import order_managment as oem
#import order_managment_candle as oemc
import chart_volume as chart
import estadisticas as st
import plotly.graph_objects as go
import find_high_volume_candles as hv
import webbrowser
import config
import os
now_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
load_dotenv()

last_100_dates_file = os.path.join('outputs', 'unique_dates.txt')

# Read the dates from the file into a list
dates = []
if os.path.exists(last_100_dates_file):
    with open(last_100_dates_file, 'r') as f:
        dates = [line.strip() for line in f.readlines()]
    print(f"✅ Loaded {len(dates)} dates from {last_100_dates_file}")

# ==== FILTRO PARA FECHAS POSTERIORES A 2023-01-02 ====
min_date = datetime.strptime('2025-04-11', '%Y-%m-%d').date()
dates = [d for d in dates if d >= '2025-04-11']

retracts = [0, 0.001, 0.002, 0.003, 0.005, 0.008, 0.01, 0.05, 0.08, 0.1, 0.5]
retro = 0.001

print(f"✅ Filtradas {len(dates)} fechas")

#dates = ['2025-01-16']
for fecha in dates:      
    print(f"\n📅 ANALIZANDO EL DIA: {fecha}")
    first_breakout_time = None
    first_breakout_price = None
    first_breakout_bool = False
    first_breakdown_time = None
    first_breakdown_price = None
    first_break_down_bool = False
    
    # Parámetros del Sistema
    #fecha = "2025-04-17"  # Fecha de inicio para el cuadradito
    hora = "16:30:00"     # Hora de inicio para el cuadradito
    lookback_min = 60    # Ventana de tiempo en minutos para el cuadradito
    entry_shift = 0     # Desplazamiento para la entrada (1 punto por encima del fractal)
    too_late_patito_negro= "21:55:00"  # Hora límite exigida para la formación del fractal patito negro para anular la entrada
    too_late_brake_fractal_pauta_plana = "19:00:00"  # Hora límite exigida para rotura del fractal patito negro para anular la entrada
    retracement = retro

    START_DATE = pd.Timestamp(fecha, tz='Europe/Madrid')
    END_DATE = pd.Timestamp(fecha, tz='Europe/Madrid')
    END_TIME = pd.Timestamp(f'{fecha} {hora}', tz='Europe/Madrid')
    START_TIME = END_TIME - pd.Timedelta(minutes=lookback_min)
    too_late_patito_negro = pd.Timestamp(f'{fecha} {too_late_patito_negro}', tz='Europe/Madrid')
    too_late_brake_fractal_pauta_plana = pd.Timestamp(f'{fecha} {too_late_patito_negro}', tz='Europe/Madrid')

    TRADING_WINDOW_TIME = (pd.Timestamp(f'{fecha} {hora}', tz='Europe/Madrid'), pd.Timestamp(f'{fecha} {too_late_patito_negro}', tz='Europe/Madrid'))

    # ====================================================
    # 📥 DESCARGA DE DATOS 
    # ====================================================
    directorio = '../DATA'
    nombre_fichero = 'ES_2015_2024_5min_timeframe.csv'
    ruta_completa = os.path.join(directorio, nombre_fichero)
    print("\n======================== 🔍 df  ==========================")
    df = pd.read_csv(ruta_completa)
    print('Fichero:', ruta_completa, 'importado')
    print(f"Características del Fichero Base: {df.shape}")

    # ====================================================
    # CREACIÓN DE UN SUBDATASET CON UN RANGO 
    # ====================================================

    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], utc=True)  # Asegura que tiene zona horaria UTC
        df.set_index('Date', inplace=True)
    df.index = df.index.tz_convert('Europe/Madrid')
    df_subset = df[(df.index.date >= START_DATE.date()) & (df.index.date <= END_DATE.date())]
    fecha_trading_sp = df_subset['Close'].iloc[-1]

    print("\n====================== 🔍 df_subset  =====================")
    print(f"Subsegmento: Creado con {len(df_subset)} registros entre {START_DATE} y {END_DATE}")
    print(f"Característica del Subsegmento: {df_subset.shape}")


    # ====================================================
    # 💣 BUSQUEDA DEL MÁXIMO Y MÍNIMO DEL CUADRADITO 
    # ====================================================
    window_df = df[(df.index >= START_TIME) & (df.index <= END_TIME)]
    if not window_df.empty:
        y0_value = window_df['Low'].min()
        y1_value = window_df['High'].max()
    opening_range = y1_value - y0_value

    # ========================================================
    # 💣 BUSQUEDA DEL MÁXIMO Y MÍNIMO DEL CUERPO DE LA VELA
    # ========================================================
    window_df = df[(df.index >= START_TIME) & (df.index <= END_TIME)]
    if not window_df.empty:
        y0_subvalue = window_df['Close'].min()
        y1_subvalue = window_df['Close'].max()
    opening_range_subvalue = y1_subvalue - y0_subvalue

    print(f"\nMàximo del Rango del Cuadradito y1_value: {y1_value}")
    print(f"Màximo del Rango del Cuadradito y1_value: {y1_subvalue}")
    print(f"Mínimo del Rango del Cuadradito y0_value: {y0_subvalue}")
    print(f"Mínimo del Rango del Cuadradito y0_value: {y0_value}")
    print(f"Rango Apertura del Cuadradito - opening_range: {opening_range}")
    print(f"Rango Apertura del Cuadradito - opening_range: {opening_range_subvalue}")

    # ==================================================================================================================================

    # Crear subdataframe después del cierre del rango
    after_open_df = df_subset[df_subset.index >= END_TIME]

    # Inicializar variables
    first_breakout_time = None
    first_breakout_price = None
    first_breakout_bool = False

    first_breakdown_time = None
    first_breakdown_price = None
    first_breakdown_bool = False

    # Buscar breakout por encima de y1_subvalue
    breakout_rows = after_open_df[after_open_df['Close'] > y1_subvalue]
    if not breakout_rows.empty:
        first_breakout_time = breakout_rows.index[0]
        first_breakout_price = breakout_rows.iloc[0]['Close']
        first_breakout_bool = True
        print(f"⚡ Rotura High en Pre-Aviso TRUE a las: {first_breakout_time} en el precio {first_breakout_price}")

    # Buscar breakdown por debajo de y0_subvalue
    breakdown_rows = after_open_df[after_open_df['Close'] < y0_subvalue]
    if not breakdown_rows.empty:
        first_breakdown_time = breakdown_rows.index[0]
        first_breakdown_price = breakdown_rows.iloc[0]['Close']
        first_breakdown_bool = True
        print(f"⚡ Rotura Low en Pre-Aviso TRUE a las:  {first_breakdown_time} en el precio {first_breakdown_price}")

    # ====================================================
    # FIND STATS
    # ====================================================

    # Llamar a la función de estadísticas con los valores correctos
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

    # ====================================================
    # FIND HIGH VOLUME CANDLES
    # ====================================================

    df_high_volumen_candles = hv.df_high_volumen_candles(
        df_subset,
        TRADING_WINDOW_TIME,
        y0_value,
        y1_value,
        n=2, # Compara el volumen con el volumen medio de las dos anteriores velas
        factor=1 # Exige para True que  la vela actual tenga un volumen superior en un factor determinado un 1.1 es un 10% más de volumen
    )

    df_high_volumen_candles = df_high_volumen_candles[df_high_volumen_candles['Volumen_Alto']]

    # ====================================================
    # ORDER MANAGMENT
    # ====================================================

    trade_result = oem.order_management(
        after_open_df=after_open_df,
        y0_value=y0_value,
        y1_value=y1_value,
        first_breakout_time=first_breakout_time,
        first_breakout_price=first_breakout_price,
        first_breakdown_time=first_breakdown_time,
        first_breakdown_price=first_breakdown_price,
        first_breakout_bool=first_breakout_bool,
        first_breakdown_bool=first_breakdown_bool,
        retracement=retracement,          # Ejemplo: 1% retroceso
        opening_range=opening_range
    )


    df_trade_result = pd.DataFrame([trade_result])
    print("\n📌 Señales generadas por Order Management:")
    print(df_trade_result.T)
    
    # ====================================================
    # GRAFICACIÓN DE DATOS 
    # ====================================================
    titulo = f"Chart_{fecha}"       
    chart.graficar_precio(
        df_subset,
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
        df_orders=df_trade_result    # <-- este es tu DataFrame con columnas correctas
    )

# ====================================================
# SUMMARIO SEGÚN % DE RETRACEMENT
# ====================================================
# === Leer el archivo tracking_record.csv ===
tracking_file = 'outputs/tracking_record.csv'
df = pd.read_csv(tracking_file)

# Limpiar y convertir tipos numéricos si es necesario
for col in ['profit_points', 'profit_usd', 'retracement_level']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Eliminar filas vacías o sin entrada válida
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

print('\nResumen agrupado por tipo de entrada y retracement_level:\n')
print(summary.to_string(index=False))
summary.to_csv('outputs/summary_by_retracement.csv', index=False)

# --- TABLA 2: Sólo por retracement_level (ignorando long/short) ---
grouped2 = df.groupby('retracement_level')
summary2 = grouped2.agg(
    total_trades=('profit_points', 'count'),
    sum_profit_points=('profit_points', lambda x: int(round(x.sum()))),
    sum_profit_usd=('profit_usd', lambda x: round(x.sum(), 2)),
    avg_profit_points=('profit_points', lambda x: round(x.mean(), 2)),
    avg_profit_usd=('profit_usd', lambda x: round(x.mean(), 2))
).reset_index()
summary2 = summary2.sort_values('retracement_level').reset_index(drop=True)

print('\nResumen agrupado sólo por retracement_level:\n')
print(summary2.to_string(index=False))
summary2.to_csv('outputs/summary_by_retracement_only.csv', index=False)

# === Leer el archivo tracking_record.csv ===
tracking_file = 'outputs/tracking_record.csv'
df = pd.read_csv(tracking_file)

# Limpiar y convertir tipos numéricos si es necesario
for col in ['profit_points', 'profit_usd', 'retracement_level']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Eliminar filas vacías o sin entrada válida
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

# Formatea decimales SOLO para las tablas HTML (no afecta los cálculos)
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

# Crear el HTML con estilos y títulos
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





























