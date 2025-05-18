import pandas as pd
import os

def order_managment(
    df_subset: pd.DataFrame,
    y0_value: float,
    y1_value: float,
    END_TIME,
    first_breakout_time: pd.Timestamp,
    first_breakout_price: float,
    first_breakdown_time: pd.Timestamp,
    first_breakdown_price: float,
    df_high_volumen_candles: pd.DataFrame,
    target_profit: float = 15,
    stop_lost: float = 4,
    discount_short: float = -0.20,
    discount_long: float = 20
) -> pd.DataFrame:

    def encontrar_entrada_validada(df_data, vol_idx, entry_type, n=2):
        idx_list = df_data.index.tolist()
        if vol_idx not in idx_list:
            return None
        start_pos = idx_list.index(vol_idx)

        for i in range(n):
            if start_pos + i >= len(df_data):
                break
            row = df_data.iloc[start_pos + i]
            ts = df_data.index[start_pos + i]

            if entry_type == 'Long' and row['Close'] > row['Open']:
                return ts, row['Close']
            elif entry_type == 'Short' and row['Close'] < row['Open']:
                return ts, row['Close']
        return None

    # ================== CALCULOS BASE ======================
    midpoint = (y1_value + y0_value) / 2
    n_lookahead = 3

    df = df_high_volumen_candles.copy()    
    df = df[df.index > END_TIME]  # 🚨 Solo velas posteriores a END_TIME

    df['Entry'] = df['Close'].apply(
        lambda x: 'Short' if x > y1_value else ('Long' if x < y0_value else None)
    )
    df = df[df['Entry'].notna()].copy()

    entradas_finales = []

    for alert_idx, row in df.iterrows():
        entry_type = row['Entry']
        valid = encontrar_entrada_validada(df_subset, alert_idx, entry_type, n=n_lookahead)
        if valid:
            entry_time, entry_price = valid
            entradas_finales.append((entry_time, entry_type, entry_price, alert_idx))

    results = []

    for entry_time, entry_type, entry_price, alert_idx in entradas_finales:
        tp = midpoint
        sl = entry_price - stop_lost if entry_type == 'Long' else entry_price + stop_lost

        after_entry = df_subset[df_subset.index > entry_time]
        max_fav = 0
        max_adv = 0
        exit_price = None
        exit_time = None
        outcome = None

        for idx, bar in after_entry.iterrows():
            high = bar['High']
            low = bar['Low']

            if entry_type == 'Long':
                if high >= tp:
                    exit_time, exit_price, outcome = idx, tp, 'TP'
                    break
                elif low <= sl:
                    exit_time, exit_price, outcome = idx, sl, 'SL'
                    break
            elif entry_type == 'Short':
                if low <= tp:
                    exit_time, exit_price, outcome = idx, tp, 'TP'
                    break
                elif high >= sl:
                    exit_time, exit_price, outcome = idx, sl, 'SL'
                    break

            max_fav = max(max_fav, high - entry_price if entry_type == 'Long' else entry_price - low)
            max_adv = max(max_adv, entry_price - low if entry_type == 'Long' else high - entry_price)

        if outcome is None and not after_entry.empty:
            last_idx = after_entry.index[-1]
            last_close = after_entry.iloc[-1]['Close']
            exit_time = last_idx
            exit_price = last_close
            outcome = 'close_at_end'

        duration = exit_time - entry_time if exit_time else None
        profit = (exit_price - entry_price) if entry_type == 'Long' else (entry_price - exit_price)
        instrument_value = 50
        profit_currency = profit * instrument_value

        pre_entry_window = df_subset[(df_subset.index > END_TIME) & (df_subset.index < entry_time)]
        break_label = False
        break_d_label = False

        if not pre_entry_window.empty:
            range_size = y1_value - y0_value
            if entry_type == 'Long':
                break_label = pre_entry_window['High'].gt(y1_value).any()
                y1_discount = y1_value - range_size * abs(discount_short)
                break_d_label = pre_entry_window['High'].gt(y1_discount).any()
            elif entry_type == 'Short':
                break_label = pre_entry_window['Low'].lt(y0_value).any()
                y0_discount = y0_value + discount_long
                break_d_label = pre_entry_window['Low'].lt(y0_discount).any()

        results.append({
            'Alert_Time': alert_idx,
            'Entry_Time': entry_time,
            'Entry': entry_type,
            'Entry_Price': entry_price,
            'TP': tp,
            'SL': sl,
            'Exit_Time': exit_time,
            'Exit_Price': exit_price,
            'Outcome': outcome,
            'Duration': duration,
            'Profit': profit,
            'Profit_$': profit_currency,
            'MFE_points': max_fav,
            'MAE_points': max_adv,
            'break_oposite': break_label,
            'break_D_oposite': break_d_label
        })

    df_orders = pd.DataFrame(results)
    os.makedirs('outputs', exist_ok=True)
    summary_file_path = os.path.join('outputs', 'summary_orders.csv')

    if os.path.exists(summary_file_path):
        existing_df = pd.read_csv(summary_file_path)
        updated_df = pd.concat([existing_df, df_orders], ignore_index=True)
        updated_df.to_csv(summary_file_path, index=False)
        print(f"✅ Archivo actualizado: {summary_file_path}")
    else:
        df_orders.to_csv(summary_file_path, index=False)
        print(f"✅ Archivo creado: {summary_file_path}")

    return df_orders
