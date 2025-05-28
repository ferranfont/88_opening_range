import os
import pandas as pd

def estadisticas_trading(
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

    stop_out = False
    lost = None
    target_profit = False
    profit_points = None
    MFE = None
    MAE = None
    mfe_time = None
    stop_out_time = None

    df_after_entry = pd.DataFrame()
    if entry_type == 'Long' and first_breakout_time:
        df_after_entry = after_open_df[after_open_df.index >= first_breakout_time]
    elif entry_type == 'Short' and first_breakdown_time:
        df_after_entry = after_open_df[after_open_df.index >= first_breakdown_time]

    opening_range = y1_value - y0_value

    # STOP OUT y LOST
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

    # TARGET PROFIT
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

    # MFE y MAE con tiempo del MFE
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

    # SOLO CAMPOS RELEVANTES
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
        'MAE_desde_entrada': MAE
    }

    output_path = os.path.join('outputs', 'summary_stats.csv')
    os.makedirs('outputs', exist_ok=True)
    df_result = pd.DataFrame([result])
    write_header = not os.path.exists(output_path)
    df_result.to_csv(output_path, mode='a', header=write_header, index=False)

    return result
