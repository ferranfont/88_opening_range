# ES NECESARIO SACAR UNA ESTADÍSTICA POR CADA UNO DE LOS VALORS DE LA LISTA restracements

import os
import pandas as pd

def estadisticas(
    after_open_df,
    y0_value, 
    y1_value, 
    y0_subvalue, 
    y1_subvalue,
    first_breakout_time,
    first_breakout_price,
    first_breakdown_time,
    first_breakdown_price,
    first_breakout_bool,
    first_breakdown_bool,
    fecha,
    fecha_trading_sp
):
    # Determinar tipo de entrada
    if first_breakout_bool and not first_breakdown_bool:
        entry_type = 'Long'
    elif first_breakdown_bool and not first_breakout_bool:
        entry_type = 'Short'
    elif first_breakout_bool and first_breakdown_bool:
        entry_type = 'Long' if first_breakout_time < first_breakdown_time else 'Short'
    else:
        entry_type = 'None'

    # Inicializar variables
    stop_out = False
    lost = None
    target_profit = False
    profit_points = None
    MFE = None
    MAE = None
    mfe_time = None
    stop_out_time = None

    # Seleccionar df_after_entry según tipo de entrada
    df_after_entry = pd.DataFrame()
    if entry_type == 'Long' and first_breakout_time:
        df_after_entry = after_open_df[after_open_df.index >= first_breakout_time]
    elif entry_type == 'Short' and first_breakdown_time:
        df_after_entry = after_open_df[after_open_df.index >= first_breakdown_time]

    # === NUEVO: CÁLCULO CORRECTO DEL RETROCESO ===
    opening_range = y1_value - y0_value
    retroceso = 0
    RL_result = "No Pull-back"
    porcentaje_retroceso = 0

    if entry_type == 'Long' and not df_after_entry.empty and first_breakout_price is not None:
        min_low = df_after_entry['Low'].min()
        # AQUÍ ES DONDE CAMBIAS:
        min_low = max(min_low, y0_value)  # No cuenta por debajo del stop
        retroceso = max(0, first_breakout_price - min_low)
        is_stop_loss = min_low == y0_value
    elif entry_type == 'Short' and not df_after_entry.empty and first_breakdown_price is not None:
        max_high = df_after_entry['High'].max()
        # AQUÍ ES DONDE CAMBIAS:
        max_high = min(max_high, y1_value)  # No cuenta por encima del stop
        retroceso = max(0, max_high - first_breakdown_price)
        is_stop_loss = max_high == y1_value
    else:
        is_stop_loss = False


    # === STOP OUT y LOST ===
    if entry_type == 'Long' and not df_after_entry.empty and first_breakout_price is not None:
        stop_hits = df_after_entry[df_after_entry['Low'] < y0_value]
        stop_out = not stop_hits.empty
        stop_out_time = stop_hits.index[0] if stop_out else None
        lost = first_breakout_price - y0_value

    elif entry_type == 'Short' and not df_after_entry.empty and first_breakdown_price is not None:
        stop_hits = df_after_entry[df_after_entry['High'] > y1_value]
        stop_out = not stop_hits.empty
        stop_out_time = stop_hits.index[0] if stop_out else None
        lost = y1_value - first_breakdown_price

    # === TARGET PROFIT ===
    if entry_type == 'Long' and not df_after_entry.empty:
        closes_above = df_after_entry[df_after_entry['Close'] > y1_value]
        if not closes_above.empty:
            target_profit = True
            profit_points = closes_above['Close'].max() - y1_value

    elif entry_type == 'Short' and not df_after_entry.empty:
        closes_below = df_after_entry[df_after_entry['Close'] < y0_value]
        if not closes_below.empty:
            target_profit = True
            profit_points = y0_value - closes_below['Close'].min()

    # === MFE y MAE con tiempo del MFE ===
    if entry_type == 'Long' and not df_after_entry.empty and first_breakout_price is not None:
        max_high = df_after_entry['High'].max()
        MFE = max_high - first_breakout_price
        mfe_time = df_after_entry[df_after_entry['High'] == max_high].index[0]
        MAE = first_breakout_price - df_after_entry['Low'].min()

    elif entry_type == 'Short' and not df_after_entry.empty and first_breakdown_price is not None:
        min_low = df_after_entry['Low'].min()
        MFE = first_breakdown_price - min_low
        mfe_time = df_after_entry[df_after_entry['Low'] == min_low].index[0]
        MAE = df_after_entry['High'].max() - first_breakdown_price

    # === NUEVO: CÁLCULO CORRECTO DEL RETROCESO ===
    opening_range = y1_value - y0_value
    retroceso = 0
    RL_result = "No Pull-back"
    porcentaje_retroceso = 0

    if entry_type == 'Long' and not df_after_entry.empty and first_breakout_price is not None:
        min_low = df_after_entry['Low'].min()
        retroceso = max(0, first_breakout_price - min_low)
        # Stop-Loss exacto si min_low <= y0_value
        is_stop_loss = min_low <= y0_value + 1e-6
    elif entry_type == 'Short' and not df_after_entry.empty and first_breakdown_price is not None:
        max_high = df_after_entry['High'].max()
        retroceso = max(0, max_high - first_breakdown_price)
        # Stop-Loss exacto si max_high >= y1_value
        is_stop_loss = max_high >= y1_value - 1e-6
    else:
        is_stop_loss = False

    if opening_range > 0:
        porcentaje_retroceso = retroceso / opening_range
        if retroceso == 0:
            RL_result = "No Pull-back"
        elif is_stop_loss:
            RL_result = "Pull-back Stop-Loss"
        elif porcentaje_retroceso < 0.05:
            RL_result = "Pull-back <5%"
        elif porcentaje_retroceso < 0.10:
            RL_result = "Pull-back 5-10%"
        elif porcentaje_retroceso < 0.20:
            RL_result = "Pull-back 10-20%"
        elif porcentaje_retroceso < 0.25:
            RL_result = "Pull-back 20-25%"
        elif porcentaje_retroceso < 0.30:
            RL_result = "Pull-back 25-30%"
        elif porcentaje_retroceso < 0.50:
            RL_result = "Pull-back 30-50%"
        elif porcentaje_retroceso < 0.61:
            RL_result = "Pull-back 50-61%"
        elif porcentaje_retroceso < 0.75:
            RL_result = "Pull-back 61-75%"
        elif porcentaje_retroceso < 1.00:
            RL_result = "Pull-back 75-100%"
        else:
            RL_result = "Pull-back >100%"  # Solo por control, pero debería salir solo en errores de datos
    else:
        RL_result = "Opening range 0 o inválido"

    # === Pull-back_PER y su etiqueta por tramos personalizados ===
    Pull_back_PER = None
    Label_Pull_back_PER = "No Pull-back"

    if entry_type == 'Long' and first_breakout_price and first_breakout_price > 0 and not df_after_entry.empty:
        Pull_back_PER = retroceso / first_breakout_price
    elif entry_type == 'Short' and first_breakdown_price and first_breakdown_price > 0 and not df_after_entry.empty:
        Pull_back_PER = retroceso / first_breakdown_price

    if Pull_back_PER is None or Pull_back_PER == 0:
        Label_Pull_back_PER = "No Pull-back"
    elif Pull_back_PER < 0.005:
        Label_Pull_back_PER = "Pull-back <0.5%"
    elif 0.005 <= Pull_back_PER < 0.01:
        Label_Pull_back_PER = "Pull-back 0.5-1%"
    elif 0.01 <= Pull_back_PER < 0.02:
        Label_Pull_back_PER = "Pull-back 1-2%"
    elif 0.02 <= Pull_back_PER < 0.03:
        Label_Pull_back_PER = "Pull-back 2-3%"
    elif 0.03 <= Pull_back_PER < 0.04:
        Label_Pull_back_PER = "Pull-back 3-4%"
    elif 0.04 <= Pull_back_PER < 0.05:
        Label_Pull_back_PER = "Pull-back 4-5%"
    elif 0.05 <= Pull_back_PER <= 0.10:
        Label_Pull_back_PER = "Pull-back 5-10%"
    elif Pull_back_PER > 0.10:
        Label_Pull_back_PER = "Pull-back >10%"

    # === NUEVO: CÁLCULO DEL CUADRANTE DEL RETROCESO SOBRE EL RANGO ===
    zona_retroceso = "No Pull-back"
    zona_percent = 0
    if opening_range > 0:
        if entry_type == 'Long' and not df_after_entry.empty and first_breakout_price is not None:
            min_low = df_after_entry['Low'].min()
            retroceso_rango = first_breakout_price - min_low
        elif entry_type == 'Short' and not df_after_entry.empty and first_breakdown_price is not None:
            max_high = df_after_entry['High'].max()
            retroceso_rango = max_high - first_breakdown_price
        else:
            retroceso_rango = 0
        zona_percent = retroceso_rango / opening_range if opening_range > 0 else 0
        if retroceso_rango == 0:
            zona_retroceso = "Zona 0 (No Pull-back)"
        elif zona_percent <= 0.2:
            zona_retroceso = "Zona 20"
        elif zona_percent <= 0.4:
            zona_retroceso = "Zona 40"
        elif zona_percent <= 0.6:
            zona_retroceso = "Zona 60"
        elif zona_percent <= 0.8:
            zona_retroceso = "Zona 80"
        elif zona_percent <= 1.0:
            zona_retroceso = "Zona 100"
        else:
            zona_retroceso = "Zona >100"
    else:
        zona_retroceso = "Rango 0 o inválido"

    # === Resultado final con nuevos campos ===
    result = {
        'Fecha': fecha,
        'SP500_close': fecha_trading_sp,
        'entry_type': entry_type,
        'Rotura High Prematura': first_breakout_time,
        'Rotura Low Prematura': first_breakdown_time,
        'target_profit_outside_range': target_profit,
        'profit_points_outside_range': profit_points,
        'target_profit_mfe_time': mfe_time,
        'stop_out_outside_range': stop_out,
        'lost_outside_range': lost,
        'stop_out_time': stop_out_time,
        'mfe_time': mfe_time,
        'rango_apertura': opening_range,
        'subrango_apertura': y1_subvalue - y0_subvalue,
        'MFE_desde_entrada': MFE,
        'MAE_desde_entrada': MAE,
        'retroceso_absoluto': retroceso,
        'Pull-back s/ Open_range': porcentaje_retroceso,
        'Label_s/Pull-back': RL_result,
        'Pull-back_PER': Pull_back_PER,
        'Label_Pull-back_PER': Label_Pull_back_PER,
        'Zona_Retroceso_Rango': zona_retroceso,
        'Zona_Retroceso_%': zona_percent
    }

    # === Guardar en CSV línea a línea ===
    output_path = os.path.join('outputs', 'summary_stats.csv')
    os.makedirs('outputs', exist_ok=True)
    df_result = pd.DataFrame([result])
    write_header = not os.path.exists(output_path)
    df_result.to_csv(output_path, mode='a', header=write_header, index=False)

    return result
