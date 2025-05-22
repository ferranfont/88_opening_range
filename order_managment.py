# order_management.py

import os
import pandas as pd

def order_management(
    after_open_df,
    y0_value, 
    y1_value,
    first_breakout_time,
    first_breakout_price,
    first_breakdown_time,
    first_breakdown_price,
    first_breakout_bool,
    first_breakdown_bool,
    retracement,    # e.g., 0.01 for 1% retracement
    opening_range   # distancia objetivo en puntos
):
    """
    Sistema Andrea Unger: 
    - Activa vigilancia tras breakout/breakdown.
    - Entrada real SOLO tras retroceso (retracement).
    - Salida por target, stop o close de la última vela del día.
    - Guarda cada trade en outputs/tracking_record.csv.

    Returns:
        dict con detalles de la operación.
    """

    # 1. Determinar tipo de entrada
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
            'entry_time': None,
            'entry_price': None,
            'exit_time': None,
            'exit_price': None,
            'target_profit': None,
            'stop_lost': None,
            'profit_points': None,
            'profit_usd': None,
            'trade_time': None,
            'retracement_level': retracement,
            'label': 'No activation'
        }
        save_trade_result(result)
        return result

    # 2. Calcular precio de entrada según retracement
    if entry_type == 'Long':
        entry_price = activation_price * (1 - retracement)
    elif entry_type == 'Short':
        entry_price = activation_price * (1 + retracement)
    else:
        entry_price = None

    # 3. Buscar ejecución de entrada tras la activación
    df_after_activation = after_open_df[after_open_df.index > activation_time].copy()
    entry_time, executed_entry_price = None, None

    if entry_type == 'Long':
        # Busca la primera vela cuyo LOW <= entry_price tras la activación
        for idx, row in df_after_activation.iterrows():
            if row['Low'] <= entry_price:
                entry_time = idx
                executed_entry_price = entry_price
                break
    elif entry_type == 'Short':
        # Busca la primera vela cuyo HIGH >= entry_price tras la activación
        for idx, row in df_after_activation.iterrows():
            if row['High'] >= entry_price:
                entry_time = idx
                executed_entry_price = entry_price
                break

    if entry_time is None:
        result = {
            'entry_type': entry_type,
            'activation_time': activation_time,
            'activation_price': activation_price,
            'entry_time': None,
            'entry_price': entry_price,
            'exit_time': None,
            'exit_price': None,
            'target_profit': None,
            'stop_lost': None,
            'profit_points': None,
            'profit_usd': None,
            'trade_time': None,
            'retracement_level': retracement,
            'label': 'No Entry'
        }
        save_trade_result(result)
        return result

    # 4. Calcular targets y stops según tipo de entrada
    if entry_type == 'Long':
        target_profit = executed_entry_price + opening_range
        stop_lost = y0_value
    elif entry_type == 'Short':
        target_profit = executed_entry_price - opening_range
        stop_lost = y1_value

    # 5. Buscar salida por target, stop o final de día
    df_after_entry = df_after_activation[df_after_activation.index >= entry_time].copy()
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

    # Si no sale ni por target ni por stop, cierra al final del día
    if exit_time is None:
        final_idx = df_after_entry.index[-1]
        final_row = df_after_entry.iloc[-1]
        exit_time = final_idx
        exit_price = final_row['Close']
        label = 'EOD'

    # 6. Calcular profit (en puntos y en $)
    if entry_type == 'Long':
        profit_points = exit_price - executed_entry_price
    elif entry_type == 'Short':
        profit_points = executed_entry_price - exit_price
    else:
        profit_points = None

    profit_usd = profit_points * 50 if profit_points is not None else None

    # 7. Calcular duración del trade
    if (entry_time is not None) and (exit_time is not None):
        trade_time = (pd.Timestamp(exit_time) - pd.Timestamp(entry_time))
    else:
        trade_time = None

    # 8. Compilar resultados
    result = {
        'entry_type': entry_type,
        'activation_time': activation_time,
        'activation_price': activation_price,
        'entry_time': entry_time,
        'entry_price': executed_entry_price,
        'exit_time': exit_time,
        'exit_price': exit_price,
        'target_profit': target_profit,
        'stop_lost': stop_lost,
        'profit_points': profit_points,
        'profit_usd': profit_usd,
        'trade_time': trade_time,
        'retracement_level': retracement,
        'label': label
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
