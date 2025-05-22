import os
import pandas as pd

def order_management_trading(
    after_open_df,
    y0_value,
    y1_value,
    first_breakout_time,
    first_breakout_price,
    first_breakdown_time,
    first_breakdown_price,
    first_breakout_bool,
    first_breakdown_bool,
    retracements,     # Lista: ej. [0, 0.004]
    opening_range     # target profit en puntos
):
    """
    Sistema Andrea Unger (Multi-Entry Retracements):
    - Tras activación, ejecuta varias entradas al alcanzar distintos niveles de retracement (vector).
    - Target profit sobre el PRECIO MEDIO DE ENTRADA.
    - Stop loss común (y0_value para long, y1_value para short).
    - Guarda las coordenadas de cada entrada para graficar.
    - Calcula el profit en USD multiplicado por el número de entradas (lotes).
    - Si entry_type=Long, nunca compra si el precio está por debajo de y0_value.
    - Si entry_type=Short, nunca vende si el precio está por encima de y1_value.
    - Añade num_positions como número de entradas hechas ese día.
    """
    results = []

    # 1. Determinar tipo de entrada y precio de activación
    if first_breakout_bool and (not first_breakdown_bool or (first_breakout_time < first_breakdown_time)):
        entry_type = 'Long'
        activation_time = first_breakout_time
        activation_price = first_breakout_price
    elif first_breakdown_bool and (not first_breakout_bool or (first_breakdown_time < first_breakout_time)):
        entry_type = 'Short'
        activation_time = first_breakdown_time
        activation_price = first_breakdown_price
    else:
        # No activación
        result = {
            'entry_type': None,
            'activation_time': None,
            'activation_price': None,
            'entry_times': [],
            'entry_prices': [],
            'average_entry_price': None,
            'exit_time': None,
            'exit_price': None,
            'target_profit': None,
            'stop_lost': None,
            'profit_points': None,
            'profit_usd': None,
            'trade_time': None,
            'retracement_levels': retracements,
            'label': 'No activation',
            'entry_coords': [],
            'num_positions': 0   # <--- Añadido aquí
        }
        save_trade_result(result)
        return result

    # 2. Calcular precios de entrada para cada retracement
    entry_prices = []
    for r in retracements:
        if entry_type == 'Long':
            entry_prices.append(activation_price * (1 - r))
        elif entry_type == 'Short':
            entry_prices.append(activation_price * (1 + r))

    # 3. Buscar ejecuciones para cada nivel de retracement
    df_after_activation = after_open_df[after_open_df.index > activation_time].copy()
    entry_times = []
    executed_entry_prices = []
    entry_coords = []  # Guarda (timestamp, entry_price, retracement_level)

    df_temp = df_after_activation.copy()
    for i, entry_price in enumerate(entry_prices):
        if entry_type == 'Long':
            # No buscar long entries si el precio está por debajo del soporte (y0_value)
            possible_longs = df_temp[df_temp['Low'] >= y0_value]
            entry_time = None
            for idx, row in possible_longs.iterrows():
                if row['Low'] <= entry_price:
                    entry_time = idx
                    executed_entry_prices.append(entry_price)
                    entry_times.append(entry_time)
                    entry_coords.append((entry_time, entry_price, retracements[i]))
                    df_temp = df_temp[df_temp.index > idx]
                    break
        elif entry_type == 'Short':
            # No buscar short entries si el precio está por encima de la resistencia (y1_value)
            possible_shorts = df_temp[df_temp['High'] <= y1_value]
            entry_time = None
            for idx, row in possible_shorts.iterrows():
                if row['High'] >= entry_price:
                    entry_time = idx
                    executed_entry_prices.append(entry_price)
                    entry_times.append(entry_time)
                    entry_coords.append((entry_time, entry_price, retracements[i]))
                    df_temp = df_temp[df_temp.index > idx]
                    break

    # Si no hay entradas, guardar como No Entry
    if not entry_times:
        result = {
            'entry_type': entry_type,
            'activation_time': activation_time,
            'activation_price': activation_price,
            'entry_times': [],
            'entry_prices': [],
            'average_entry_price': None,
            'exit_time': None,
            'exit_price': None,
            'target_profit': None,
            'stop_lost': None,
            'profit_points': None,
            'profit_usd': None,
            'trade_time': None,
            'retracement_levels': retracements,
            'label': 'No Entry',
            'entry_coords': [],
            'num_positions': 0   # <--- Añadido aquí
        }
        save_trade_result(result)
        return result

    # 4. Precio medio de entrada
    average_entry_price = sum(executed_entry_prices) / len(executed_entry_prices)

    # 5. Target y Stop comunes para todo el bloque
    if entry_type == 'Long':
        target_profit = average_entry_price + opening_range
        stop_lost = y0_value
    elif entry_type == 'Short':
        target_profit = average_entry_price - opening_range
        stop_lost = y1_value

    # 6. Buscar salida por target, stop o EOD desde la ÚLTIMA entrada (más conservador)
    last_entry_time = entry_times[-1]
    df_after_entry = df_after_activation[df_after_activation.index >= last_entry_time].copy()
    exit_time = None
    exit_price = None
    label = None

    if entry_type == 'Long':
        for idx, row in df_after_entry.iterrows():
            if row['High'] >= target_profit:
                exit_time = idx
                exit_price = target_profit
                label = 'Target Profit'
                break
            elif row['Low'] <= stop_lost:
                exit_time = idx
                exit_price = stop_lost
                label = 'Stop Lost'
                break
    elif entry_type == 'Short':
        for idx, row in df_after_entry.iterrows():
            if row['Low'] <= target_profit:
                exit_time = idx
                exit_price = target_profit
                label = 'Target Profit'
                break
            elif row['High'] >= stop_lost:
                exit_time = idx
                exit_price = stop_lost
                label = 'Stop Lost'
                break

    # Si no hay salida por TP o SL, cierre a final del día
    if exit_time is None:
        final_idx = df_after_entry.index[-1]
        final_row = df_after_entry.iloc[-1]
        exit_time = final_idx
        exit_price = final_row['Close']
        label = 'EOD'

    # 7. Profit sobre todas las posiciones (en puntos y en $)
    lots = len(entry_times)
    if entry_type == 'Long':
        profit_points = exit_price - average_entry_price
    elif entry_type == 'Short':
        profit_points = average_entry_price - exit_price
    else:
        profit_points = None

    profit_usd = profit_points * lots * 50 if profit_points is not None else None

    # 8. Duración del trade: de la primera entrada a la salida
    if entry_times and exit_time is not None:
        trade_time = (pd.Timestamp(exit_time) - pd.Timestamp(entry_times[0]))
    else:
        trade_time = None

    # 9. Compilar resultados
    result = {
        'entry_type': entry_type,
        'activation_time': activation_time,
        'activation_price': activation_price,
        'entry_times': entry_times,
        'entry_prices': executed_entry_prices,
        'average_entry_price': average_entry_price,
        'exit_time': exit_time,
        'exit_price': exit_price,
        'target_profit': target_profit,
        'stop_lost': stop_lost,
        'profit_points': profit_points,
        'profit_usd': profit_usd,
        'trade_time': trade_time,
        'retracement_levels': retracements,
        'label': label,
        'entry_coords': entry_coords,  # Lista de tuplas (timestamp, entry_price, retracement_level)
        'num_positions': lots   # <--- Añadido aquí
    }

    save_trade_result(result)
    return result

def save_trade_result(result):
    """Guarda la operación en outputs/tracking_record.csv"""
    output_path = os.path.join('outputs', 'tracking_record.csv')
    os.makedirs('outputs', exist_ok=True)
    df_result = pd.DataFrame([result])
    write_header = not os.path.exists(output_path)
    df_result.to_csv(output_path, mode='a', header=write_header, index=False)
