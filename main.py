# ANDREA UNGER TRADING SYSTEM BREAK OUT OPENING RANGE
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import order_managment as oem
import order_managment_candle as oemc
import chart_volume as chart
import estadisticas as st
import plotly.graph_objects as go
import find_high_volume_candles as hv
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

#dates = ['2025-04-28']
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
    entry_shift = 3     # Desplazamiento para la entrada (1 punto por encima del fractal)
    too_late_patito_negro= "21:55:00"  # Hora límite exigida para la formación del fractal patito negro para anular la entrada
    too_late_brake_fractal_pauta_plana = "19:00:00"  # Hora límite exigida para rotura del fractal patito negro para anular la entrada

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
        fecha=fecha
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

    '''
    # ====================================================
    # ORDER MANAGMENT
    # ====================================================
    df_orders = oemc.order_managment(
        after_open_df,
        y0_value,
        y1_value,
        y0_subvalue,
        y1_subvalue,
        END_TIME,
        first_breakout_time,
        first_breakout_price,
        first_breakdown_time,
        first_breakdown_price
    )
    print("\n📌 Señales generadas por Order Management:")
    print(df_orders.T,"\n")
    '''
    # ====================================================
    # GRAFICACIÓN DE DATOS 
    # ====================================================
    titulo = f"Chart_{fecha}"       
    chart.graficar_precio(df_subset, too_late_patito_negro, titulo, START_TIME, END_TIME, y0_value, y1_value, y0_subvalue, y1_subvalue, first_breakout_time, first_breakout_price, first_breakdown_time, first_breakdown_price, df_high_volumen_candles)



















































