import os
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def graficar_precio(
    df, 
    too_late_patito_negro, 
    titulo, 
    START_TIME, 
    END_TIME, 
    y0_value, 
    y1_value,  
    y0_subvalue, 
    y1_subvalue, 
    first_breakout_time=None, 
    first_breakout_price=None, 
    first_breakdown_time=None, 
    first_breakdown_price=None, 
    high_volume_df=None, 
    df_orders=None
):
    if df.empty or not all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
        print("❌ DataFrame vacío o faltan columnas OHLC.")
        return

    os.makedirs("charts", exist_ok=True)

    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], utc=True)
        df.set_index('Date', inplace=True)
    df.index = df.index.tz_convert('Europe/Madrid')

    expansion = 0.38
    y1_expansion = y1_value + (y1_value - y0_value) * expansion
    y0_expansion = y0_value - (y1_value - y0_value) * expansion
    opening_range = y1_value - y0_value
    midpoint = (y1_value + y0_value) / 2

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.805, 0.20],
        vertical_spacing=0,
        subplot_titles=(titulo, '')
    )

    # --- Candlestick chart
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        increasing=dict(line=dict(color='black'), fillcolor='rgba(57, 255, 20, 0.5)'),
        decreasing=dict(line=dict(color='black'), fillcolor='red'),
        hoverinfo='none'
    ), row=1, col=1)

    # --- Volumen bar (row 2)
    if 'Volumen' in df.columns:
        fig.add_trace(go.Bar(
            x=df.index,
            y=df['Volumen'],
            marker_color='blue',
            opacity=0.5,
            hoverinfo='skip',
            name='Volumen'
        ), row=2, col=1)

    # --- Opening range rectangle
    fig.add_shape(type="rect", x0=START_TIME, x1=END_TIME, y0=y0_value, y1=y1_value,
                  xref='x', yref='y1', line=dict(color='lightblue', width=1),
                  fillcolor='rgba(173, 216, 230, 0.5)', layer='below')
    
    # --- Closing range rectangle
    fig.add_shape(type="rect", x0=START_TIME, x1=END_TIME, y0=y0_subvalue, y1=y1_subvalue,
                  xref='x', yref='y1', line=dict(color='lightblue', width=1),
                  fillcolor='rgba(173, 216, 230, 0.5)', layer='below')

    # --- Vertical lines
    fig.add_shape(type="line", x0=START_TIME, x1=START_TIME, y0=0, y1=1, xref="x", yref="paper", line=dict(color="blue", width=1), opacity=0.5)
    fig.add_shape(type="line", x0=END_TIME, x1=END_TIME, y0=0, y1=1, xref="x", yref="paper", line=dict(color="grey", width=1), opacity=0.5)
    fig.add_shape(type="line", x0=too_late_patito_negro, x1=too_late_patito_negro, y0=0, y1=1, xref="x", yref="paper", line=dict(color="grey", width=1), opacity=0.5)

    # --- Horizontal reference lines
    fig.add_shape(type="line", x0=END_TIME, x1=too_late_patito_negro, y0=midpoint, y1=midpoint, xref="x", yref="y1", line=dict(color="grey", width=1,dash="dot"), opacity=0.6) 
    fig.add_shape(type="line", x0=END_TIME, x1=too_late_patito_negro, y0=y1_value, y1=y1_value, xref="x", yref="y1", line=dict(color="blue", width=1), opacity=0.7)  
    fig.add_shape(type="line", x0=END_TIME, x1=too_late_patito_negro, y0=y0_value, y1=y0_value, xref="x", yref="y1", line=dict(color="blue", width=1), opacity=0.7)  
    fig.add_shape(type="line", x0=END_TIME, x1=too_late_patito_negro, y0=y1_subvalue, y1=y1_subvalue, xref="x", yref="y1", line=dict(color="blue", width=1, dash="dot"), opacity=0.7)  
    fig.add_shape(type="line", x0=END_TIME, x1=too_late_patito_negro, y0=y0_subvalue, y1=y0_subvalue, xref="x", yref="y1", line=dict(color="blue", width=1, dash="dot"), opacity=0.7)  

    # --- Markers for breakout/breakdown
    if first_breakout_time and first_breakout_price:
        fig.add_trace(go.Scatter(
            x=[first_breakout_time],
            y=[first_breakout_price+1],
            mode='markers',
            marker=dict(color='orange', size=14, symbol='hourglass'),
            name='First Breakout'
        ), row=1, col=1)

    if first_breakdown_time and first_breakdown_price:
        fig.add_trace(go.Scatter(
            x=[first_breakdown_time],
            y=[first_breakdown_price-1],
            mode='markers',
            marker=dict(color='DarkOrange', size=14, symbol='hourglass'),
            name='First Breakdown'
        ), row=1, col=1)
    
    # --- Markers for high volume candles
    if high_volume_df is not None and not high_volume_df.empty:
        fig.add_trace(go.Scatter(
            x=high_volume_df.index,
            y=high_volume_df['Close']-1,
            mode='markers',
            marker=dict(symbol='circle', color='blue', size=10),
            name='High Volume Candles'
        ), row=1, col=1)

    # --- Entry/Exit Orders and LINES for ALL ENTRIES
    if df_orders is not None and not df_orders.empty:
        for _, row in df_orders.iterrows():
            # Multi-entrada: listas de entry_times, entry_prices, retracement_levels
            if 'entry_times' in row and 'entry_prices' in row:
                entry_times = row['entry_times']
                entry_prices = row['entry_prices']
                retracement_levels = row['retracement_levels'] if 'retracement_levels' in row else [None]*len(entry_times)
                # Marca todas las entradas y pinta líneas desde cada entrada a la salida
                if isinstance(entry_times, list) and isinstance(entry_prices, list):
                    for t, p, r in zip(entry_times, entry_prices, retracement_levels):
                        if pd.notnull(t) and pd.notnull(p):
                            color = 'limegreen' if row['entry_type'] == 'Long' else 'red'
                            symbol = 'triangle-up' if row['entry_type'] == 'Long' else 'triangle-down'
                            # Entrada (con texto retracement)
                            fig.add_trace(go.Scatter(
                                x=[t],
                                y=[p],
                                mode='markers+text',
                                marker=dict(color=color, size=18, symbol=symbol),
                                text=[f"r={r:.3f}" if r is not None else ""],
                                textposition="top center",
                                name='Entry'
                            ), row=1, col=1)
                            # Línea de esta entrada a la salida (si existe salida)
                            if 'exit_time' in row and pd.notnull(row['exit_time']) and 'exit_price' in row and pd.notnull(row['exit_price']):
                                fig.add_trace(go.Scatter(
                                    x=[t, row['exit_time']],
                                    y=[p, row['exit_price']],
                                    mode='lines',
                                    line=dict(color='gray', width=1, dash='dot'),
                                    name='Entry to Exit'
                                ), row=1, col=1)
            # Salida (única)
            if 'exit_time' in row and pd.notnull(row['exit_time']) and 'exit_price' in row and pd.notnull(row['exit_price']):
                fig.add_trace(go.Scatter(
                    x=[row['exit_time']],
                    y=[row['exit_price']],
                    mode='markers',
                    marker=dict(color='black', size=14, symbol='x'),
                    name='Exit'
                ), row=1, col=1)

    fig.update_layout(
        dragmode='pan',
        title=titulo,
        xaxis=dict(showgrid=False, showline=True, linewidth=1, linecolor='lightgrey', mirror=True),
        yaxis=dict(title="Precio", showgrid=False, showline=True, linewidth=1, linecolor='lightgrey', mirror=True),
        xaxis2=dict(showgrid=False, showline=True, linewidth=1, linecolor='lightgrey', mirror=False),
        yaxis2=dict(title="", showgrid=False, showline=True, linewidth=1, linecolor='lightgrey', mirror=True),
        xaxis_rangeslider_visible=False,
        width=1600,
        height=int(1500 * 0.6),
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(size=12, color="black"),
        plot_bgcolor='rgba(255,255,255,0.05)',
        paper_bgcolor='rgba(240,240,240,0.6)'
    )

    fig.update_traces(showlegend=False)
    config = dict(scrollZoom=True)

    output_file = f'charts/{titulo}.html'
    fig.write_html(output_file, config=config)
    print(f"📁 Gráfico interactivo guardado como {output_file}")

    # Guardar el HTML sin abrir navegador
    fig.write_html(output_file, config=config, auto_open=False)
    print(f"📁 Gráfico interactivo guardado como {output_file}")

    # COMENTAR PARA NO SATURAR LA KERNEL DEL ORDENADOR
    import webbrowser
    # webbrowser.open('file://' + os.path.realpath(output_file))    <------------ COMENTAR PARA  NO SATURAR LA KERNEL
    
