from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import order_managment_zonas as omz
import chart_volume as chart
import estadisticas_trading as stz
import find_high_volume_candles as hv
import webbrowser
import os

now_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
load_dotenv()

# === CONFIGURACIÓN DE GRID ===
last_100_dates_file = os.path.join('outputs', 'unique_dates.txt')
retracts = [0]

# === LIMPIEZA DE TRACKING ===
tracking_file = 'outputs/tracking_record.csv'
if os.path.exists(tracking_file):
    os.remove(tracking_file)

# === LECTURA DE FECHAS ===
dates = []
if os.path.exists(last_100_dates_file):
    with open(last_100_dates_file, 'r') as f:
        dates = [line.strip() for line in f.readlines()]
    print(f"✅ Loaded {len(dates)} dates from {last_100_dates_file}")

dates = [d for d in dates if d >= '2015-01-10']
print(f"✅ Filtradas {len(dates)} fechas")

#dates = ['2023-10-02', '2023-10-03', '2023-10-04', '2023-10-05', '2023-10-06']

for retracement in retracts:
    print(f"\n=== PROBANDO RETRACEMENT: {retracement} ===")
    for fecha in dates:
        print(f"\n📅 ANALIZANDO EL DIA: {fecha} | Retracement: {retracement}")
        hora = "16:30:00"                                                               #VALOR UNGER == 16:30:00 H
        lookback_min = 60
        START_DATE = pd.Timestamp(fecha, tz='Europe/Madrid')
        END_DATE = pd.Timestamp(fecha, tz='Europe/Madrid')
        END_TIME = pd.Timestamp(f'{fecha} {hora}', tz='Europe/Madrid')
        START_TIME = END_TIME - pd.Timedelta(minutes=lookback_min)
        too_late_patito_negro = pd.Timestamp(f'{fecha} 21:55:00', tz='Europe/Madrid')
        limit_time = END_TIME + pd.Timedelta(minutes=90)
        strength_target = 9       # aquí marcamos la fortaleza exigida para emplazar una segunda entrada
        TRADING_WINDOW_TIME = (END_TIME, too_late_patito_negro)

        # === DATOS ===
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

        # === RANGOS ===
        window_df = df[(df.index >= START_TIME) & (df.index <= END_TIME)]
        if not window_df.empty:
            y0_value = window_df['Low'].min()
            y1_value = window_df['High'].max()
        else:
            continue

        y0_subvalue = window_df['Close'].min()
        y1_subvalue = window_df['Close'].max()
        opening_range = y1_value - y0_value

        # === DATOS POST-APERTURA ===
        after_open_df = df_subset[df_subset.index >= END_TIME]

        # === DETECCIÓN BREAKOUT/BREAKDOWN ===
        first_breakout_time, first_breakout_price, first_breakout_bool = None, None, False
        first_breakdown_time, first_breakdown_price, first_breakdown_bool = None, None, False

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

        # === ESTADÍSTICAS ===
        resultado = stz.estadisticas_trading(
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

        # === HIGH VOLUME CANDLES (OPCIONAL) ===
        df_high_volumen_candles = hv.df_high_volumen_candles(
            df_subset,
            TRADING_WINDOW_TIME,
            y0_value,
            y1_value,
            n=2,
            factor=1
        )
        df_high_volumen_candles = df_high_volumen_candles[df_high_volumen_candles['Volumen_Alto']]

        # === ORDER MANAGEMENT Y TRACKING ===
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

        # === GRAFICACIÓN SOLO SI HAY TRADES ===
        if not df_trade_result.empty:
            entry_type = df_trade_result.iloc[0]['entry_type'] if 'entry_type' in df_trade_result.columns else None
            titulo = f"Chart_{fecha}_retro_{retracement}"
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
        else:
            print("No hay señales generadas por Order Management ZONAS para esta fecha.")

# === ACUMULACIÓN PROFIT IN USD ===

# Lee tu archivo
df = pd.read_csv('outputs/tracking_record.csv')

# Asegúrate de que la columna 'profit_usd' es numérica
df['profit_usd'] = pd.to_numeric(df['profit_usd'], errors='coerce').fillna(0)

# Calcula la suma acumulada
df['cum_profit_usd'] = df['profit_usd'].cumsum()

# Guarda el resultado (opcional)
df.to_csv('outputs/tracking_record.csv', index=False)

