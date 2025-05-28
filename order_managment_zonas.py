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
    strength_target=7,
    prev_cum_profit_usd=0
):
    fraction = opening_range / 10
    trades = []
    columns = [
        'entry_type', 'entry_time', 'entry_price', 'zona', 'trigger',
        'exit_time', 'exit_price',
        'average_entry_price', 'entry_times', 'entry_prices', 'num_positions',
        'retracement_level', 'stop_loss', 'output_tag', 'profit_points',
        'profit_usd', 'cum_profit_usd', 'time_in'
    ]

    breakout_rows = after_open_df[(after_open_df['Close'] > y1_subvalue) & (after_open_df.index <= limit_time)]
    breakdown_rows = after_open_df[(after_open_df['Close'] < y0_subvalue) & (after_open_df.index <= limit_time)]

    breakout_time = breakout_rows.index[0] if not breakout_rows.empty else pd.NaT
    breakdown_time = breakdown_rows.index[0] if not breakdown_rows.empty else pd.NaT

    is_long = False
    is_short = False
    start_idx = None

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
            'retracement_level': retracement,
            'stop_loss': y1_value - 4 * fraction
        })
        is_long = True
        start_idx = after_open_df.index.get_loc(breakout_time) + 1

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
            'retracement_level': retracement,
            'stop_loss': y0_value + 4 * fraction
        })
        is_short = True
        start_idx = after_open_df.index.get_loc(breakdown_time) + 1

    else:
        df = pd.DataFrame(columns=columns)
        return df

    # === Lógica de fuerza SOLO después de la ruptura ===
    subdf = after_open_df.iloc[start_idx:]
    max_strength_entries = 1
    strength_entries = 0
    allow_strength_entry = True
    strength = 0
    entry_times = []
    entry_prices = []
    zona_str = []

    suelo_c_long = y1_value - 3 * fraction
    suelo_b_long = y1_value - 2 * fraction
    suelo_a_long = y1_value - fraction
    techo_a_long = y1_value

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

        # --- LONG Fuerza ---
        if is_long:
            if close > y1_value:
                allow_strength_entry = True

            if strength_entries >= max_strength_entries or not allow_strength_entry:
                continue

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
                avg_entry = np.mean(entry_prices)
                trades.append({
                    'entry_type': 'Long',
                    'entry_time': idx,
                    'entry_price': close,
                    'zona': zona_str[-1] if zona_str else "A",
                    'trigger': f'Strength>={strength_target}',
                    'exit_time': np.nan,
                    'exit_price': np.nan,
                    'average_entry_price': avg_entry,
                    'entry_times': entry_times.copy(),
                    'entry_prices': entry_prices.copy(),
                    'num_positions': len(entry_times),
                    'retracement_level': retracement,
                    'stop_loss': y1_value - 4 * fraction
                })
                strength_entries += 1
                allow_strength_entry = False
                strength = 0
                entry_times = []
                entry_prices = []
                zona_str = []

        # --- SHORT Fuerza ---
        if is_short:
            if close < y0_value:
                allow_strength_entry = True

            if strength_entries >= max_strength_entries or not allow_strength_entry:
                continue

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
                avg_entry = np.mean(entry_prices)
                trades.append({
                    'entry_type': 'Short',
                    'entry_time': idx,
                    'entry_price': close,
                    'zona': zona_str[-1] if zona_str else "A",
                    'trigger': f'Strength>={strength_target}',
                    'exit_time': np.nan,
                    'exit_price': np.nan,
                    'average_entry_price': avg_entry,
                    'entry_times': entry_times.copy(),
                    'entry_prices': entry_prices.copy(),
                    'num_positions': len(entry_times),
                    'retracement_level': retracement,
                    'stop_loss': y0_value + 4 * fraction
                })
                strength_entries += 1
                allow_strength_entry = False
                strength = 0
                entry_times = []
                entry_prices = []
                zona_str = []

    # ======= RE-CALCULAR TP/SL SOBRE EL PROMEDIO DE ENTRADAS DEL DÍA ==========
    cum_profit = prev_cum_profit_usd
    if len(trades) > 0:
        all_entry_prices = []
        for trade in trades:
            all_entry_prices.extend([float(p) for p in trade['entry_prices']])
        avg_price = np.mean(all_entry_prices)
        take_profit_long = avg_price + opening_range * 0.1
        take_profit_short = avg_price - opening_range * 0.1

        for i, trade in enumerate(trades):
            salida_idx = list(after_open_df.index).index(pd.to_datetime(trade['entry_time'])) + 1
            salida_df = after_open_df.iloc[salida_idx:]
            exit_found = False
            tag = None
            # --- Exit loop
            if trade['entry_type'] == 'Long':
                target = take_profit_long
                stop = trade['stop_loss']
                for exit_idx, exit_row in salida_df.iterrows():
                    if exit_row['Low'] <= stop:
                        trades[i]['exit_time'] = exit_idx
                        trades[i]['exit_price'] = stop
                        tag = "stop_out"
                        exit_found = True
                        break
                    if exit_row['High'] >= target:
                        trades[i]['exit_time'] = exit_idx
                        trades[i]['exit_price'] = target
                        tag = "target_profit"
                        exit_found = True
                        break
            else:
                target = take_profit_short
                stop = trade['stop_loss']
                for exit_idx, exit_row in salida_df.iterrows():
                    if exit_row['High'] >= stop:
                        trades[i]['exit_time'] = exit_idx
                        trades[i]['exit_price'] = stop
                        tag = "stop_out"
                        exit_found = True
                        break
                    if exit_row['Low'] <= target:
                        trades[i]['exit_time'] = exit_idx
                        trades[i]['exit_price'] = target
                        tag = "target_profit"
                        exit_found = True
                        break
            # If not exit found, force exit on last candle (penultimate)
            if not exit_found:
                exit_idx = salida_df.index[-2] if len(salida_df) > 1 else salida_df.index[-1]
                trades[i]['exit_time'] = exit_idx
                trades[i]['exit_price'] = after_open_df.loc[exit_idx, 'Close']
                tag = "EOD"
            trades[i]['output_tag'] = tag

            # ---- Calculate profits ----
            trades[i]['profit_points'] = (
                (trades[i]['exit_price'] - trades[i]['entry_price'])
                if trades[i]['entry_type'] == 'Long'
                else (trades[i]['entry_price'] - trades[i]['exit_price'])
            )
            trades[i]['profit_usd'] = trades[i]['profit_points'] * 50
            cum_profit += trades[i]['profit_usd']
            trades[i]['cum_profit_usd'] = cum_profit

            # ---- Calculate time_in (minutes) ----
            try:
                entry_time = pd.to_datetime(trades[i]['entry_time'])
                exit_time = pd.to_datetime(trades[i]['exit_time'])
                time_in = (exit_time - entry_time).total_seconds() / 60.0
                trades[i]['time_in'] = time_in
            except Exception:
                trades[i]['time_in'] = np.nan

    df = pd.DataFrame(trades)
    for col in columns:
        if col not in df.columns:
            df[col] = np.nan
    df = df[columns]

    # ========== *** GUARDA EL CSV AQUÍ *** ==========
    if not df.empty:
        os.makedirs('outputs', exist_ok=True)
        tracking_file = 'outputs/tracking_record.csv'
        write_header = not os.path.exists(tracking_file)
        df.to_csv(tracking_file, mode='a', header=write_header, index=False)

    return df
