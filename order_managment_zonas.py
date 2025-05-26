import pandas as pd
import numpy as np
import os

def order_management_zonas(
    after_open_df,
    limit_time,
    y0_value,
    y1_value,
    y0_subvalue,
    y1_subvalue,
    opening_range,
    retracement=0,
    strength_target=5
):
    # Variables de entrada
    fraction = opening_range / 10
    trades = []
    columns = [
        'entry_type', 'entry_time', 'entry_price', 'zona', 'trigger',
        'exit_time', 'exit_price',
        'average_entry_price', 'entry_times', 'entry_prices', 'num_positions', 'retracement_level'
    ]

    # 1. Detectar primer breakout o breakdown
    breakout_rows = after_open_df[(after_open_df['Close'] > y1_subvalue) & (after_open_df.index <= limit_time)]
    breakdown_rows = after_open_df[(after_open_df['Close'] < y0_subvalue) & (after_open_df.index <= limit_time)]

    breakout_time = breakout_rows.index[0] if not breakout_rows.empty else pd.NaT
    breakdown_time = breakdown_rows.index[0] if not breakdown_rows.empty else pd.NaT

    is_long = False
    is_short = False

    # --- ENTRADA BREAKOUT ---
    if breakout_time is not pd.NaT and (breakdown_time is pd.NaT or breakout_time < breakdown_time):
        price = breakout_rows.iloc[0]['Close']
        trades.append({
            'entry_type': 'Long',
            'entry_time': breakout_time,
            'entry_price': price,
            'zona': 'Breakout',
            'trigger': 'Breakout',
            'exit_time': np.nan,
            'exit_price': np.nan,
            'average_entry_price': price,
            'entry_times': [str(breakout_time)],
            'entry_prices': [price],
            'num_positions': 1,
            'retracement_level': retracement
        })
        is_long = True
        start_idx = after_open_df.index.get_loc(breakout_time) + 1

        # --- BUSCAR TP/SL para Breakout ---
        salida_df = after_open_df.iloc[start_idx:]
        for exit_idx, exit_row in salida_df.iterrows():
            target = price + opening_range
            stop = price - opening_range
            if exit_row['High'] >= target:
                trades[-1]['exit_time'] = exit_idx
                trades[-1]['exit_price'] = target
                break
            if exit_row['Low'] <= stop:
                trades[-1]['exit_time'] = exit_idx
                trades[-1]['exit_price'] = stop
                break

    # --- ENTRADA BREAKDOWN ---
    elif breakdown_time is not pd.NaT:
        price = breakdown_rows.iloc[0]['Close']
        trades.append({
            'entry_type': 'Short',
            'entry_time': breakdown_time,
            'entry_price': price,
            'zona': 'Breakdown',
            'trigger': 'Breakdown',
            'exit_time': np.nan,
            'exit_price': np.nan,
            'average_entry_price': price,
            'entry_times': [str(breakdown_time)],
            'entry_prices': [price],
            'num_positions': 1,
            'retracement_level': retracement
        })
        is_short = True
        start_idx = after_open_df.index.get_loc(breakdown_time) + 1

        # --- BUSCAR TP/SL para Breakdown ---
        salida_df = after_open_df.iloc[start_idx:]
        for exit_idx, exit_row in salida_df.iterrows():
            target = price - opening_range
            stop = price + opening_range
            if exit_row['Low'] <= target:
                trades[-1]['exit_time'] = exit_idx
                trades[-1]['exit_price'] = target
                break
            if exit_row['High'] >= stop:
                trades[-1]['exit_time'] = exit_idx
                trades[-1]['exit_price'] = stop
                break

    else:
        # Si no hay ruptura ni por arriba ni por abajo, devuelve DataFrame vacío estándar
        df = pd.DataFrame(columns=columns)
        tracking_file = 'outputs/tracking_record.csv'
        os.makedirs('outputs', exist_ok=True)
        if not os.path.exists(tracking_file):
            df.to_csv(tracking_file, mode='a', header=True, index=False)
        return df

    # === Lógica de fuerza SOLO después de la ruptura ===
    subdf = after_open_df.iloc[start_idx:]
    strength = 0
    entry_times = []
    entry_prices = []
    zona_str = []

    # Límites zona LONG
    suelo_c_long = y1_value - 3 * fraction
    suelo_b_long = y1_value - 2 * fraction
    suelo_a_long = y1_value - fraction
    techo_a_long = y1_value

    # Límites zona SHORT
    techo_c_short = y0_value + 3 * fraction
    techo_b_short = y0_value + 2 * fraction
    techo_a_short = y0_value + fraction
    suelo_a_short = y0_value

    for idx, row in subdf.iterrows():
        if idx > limit_time:
            break

        low = row['Low']
        high = row['High']
        close = row['Close']

        # LÓGICA LONG (fuerza)
        if is_long:
            if low < suelo_c_long:
                strength = 0
                entry_times = []
                entry_prices = []
                zona_str = []
                continue
            zona_actual = None
            if (low >= suelo_a_long) and (low < techo_a_long) and (close >= suelo_a_long):
                strength += 1
                zona_actual = "A"
            elif (low >= suelo_b_long) and (low < suelo_a_long) and (close >= suelo_b_long):
                strength += 2
                zona_actual = "B"
            elif (low >= suelo_c_long) and (low < suelo_b_long) and (close >= suelo_c_long):
                strength += 3
                zona_actual = "C"
            else:
                continue

            zona_str.append(zona_actual)
            entry_times.append(str(idx))
            entry_prices.append(close)
            if strength >= strength_target:
                avg_entry = np.mean(entry_prices[-strength_target:])
                trades.append({
                    'entry_type': 'Long',
                    'entry_time': idx,
                    'entry_price': close,
                    'zona': zona_str[-1] if zona_str else "A",
                    'trigger': f'Strength>={strength_target}',
                    'exit_time': np.nan,
                    'exit_price': np.nan,
                    'average_entry_price': avg_entry,
                    'entry_times': entry_times[-strength_target:],
                    'entry_prices': entry_prices[-strength_target:],
                    'num_positions': len(entry_times[-strength_target:]),
                    'retracement_level': retracement
                })
                # BUSCAR TP/SL para esta entrada de fuerza
                salida_idx = list(after_open_df.index).index(idx) + 1
                salida_df = after_open_df.iloc[salida_idx:]
                for exit_idx, exit_row in salida_df.iterrows():
                    target = avg_entry + opening_range
                    stop = avg_entry - opening_range
                    if exit_row['High'] >= target:
                        trades[-1]['exit_time'] = exit_idx
                        trades[-1]['exit_price'] = target
                        break
                    if exit_row['Low'] <= stop:
                        trades[-1]['exit_time'] = exit_idx
                        trades[-1]['exit_price'] = stop
                        break
                break

        # LÓGICA SHORT (fuerza)
        if is_short:
            if high > techo_c_short or close > techo_c_short:
                strength = 0
                entry_times = []
                entry_prices = []
                zona_str = []
                continue

            zona_actual = None
            if (high > suelo_a_short) and (high <= techo_a_short) and (close > suelo_a_short) and (close <= techo_a_short):
                strength += 1
                zona_actual = "A"
            elif (high > techo_a_short) and (high <= techo_b_short) and (close > techo_a_short) and (close <= techo_b_short):
                strength += 2
                zona_actual = "B"
            elif (high > techo_b_short) and (high <= techo_c_short) and (close > techo_b_short) and (close <= techo_c_short):
                strength += 3
                zona_actual = "C"
            else:
                continue

            zona_str.append(zona_actual)
            entry_times.append(str(idx))
            entry_prices.append(close)
            if strength >= strength_target:
                avg_entry = np.mean(entry_prices[-strength_target:])
                trades.append({
                    'entry_type': 'Short',
                    'entry_time': idx,
                    'entry_price': close,
                    'zona': zona_str[-1] if zona_str else "A",
                    'trigger': f'Strength>={strength_target}',
                    'exit_time': np.nan,
                    'exit_price': np.nan,
                    'average_entry_price': avg_entry,
                    'entry_times': entry_times[-strength_target:],
                    'entry_prices': entry_prices[-strength_target:],
                    'num_positions': len(entry_times[-strength_target:]),
                    'retracement_level': retracement
                })
                salida_idx = list(after_open_df.index).index(idx) + 1
                salida_df = after_open_df.iloc[salida_idx:]
                for exit_idx, exit_row in salida_df.iterrows():
                    target = avg_entry - opening_range
                    stop = avg_entry + opening_range
                    if exit_row['Low'] <= target:
                        trades[-1]['exit_time'] = exit_idx
                        trades[-1]['exit_price'] = target
                        break
                    if exit_row['High'] >= stop:
                        trades[-1]['exit_time'] = exit_idx
                        trades[-1]['exit_price'] = stop
                        break
                break

    df = pd.DataFrame(trades)
    for col in columns:
        if col not in df.columns:
            df[col] = np.nan
    df = df[columns]

    # Guardar tracking_record
    tracking_file = 'outputs/tracking_record.csv'
    os.makedirs('outputs', exist_ok=True)
    write_header = not os.path.exists(tracking_file)
    df.to_csv(tracking_file, mode='a', header=write_header, index=False)

    return df
