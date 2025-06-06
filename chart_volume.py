import os
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def graficar_precio(
    df,
    limit_time,
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
    titulo = str(titulo) + "_"+ 'Opening_Range_' + str(opening_range)


    zona = opening_range/10
    
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
                  fillcolor='rgba(173, 216, 230, 0.8)', layer='below')
    
    # Extraer entry_type dentro de la función de graficado
    entry_type = None
    if df_orders is not None and 'entry_type' in df_orders.columns:
        entry_type = df_orders.iloc[0]['entry_type'] if not df_orders.empty and 'entry_type' in df_orders.columns else None


    if entry_type == 'Long':
        # --- Rectángulo para la compresión zona A
        fig.add_shape(type="rect", x0=END_TIME, x1=limit_time, y0=y1_value-zona, y1=y1_value,
                    xref='x', yref='y1', line=dict(color='green', width=0),
                    fillcolor='rgba(119, 221, 119, 0.2)', layer='below')
        # --- Rectángulo para la compresión zona B
        fig.add_shape(type="rect", x0=END_TIME, x1=limit_time, y0=y1_value-(zona*2), y1=y1_value-zona,
                    xref='x', yref='y1', line=dict(color='green', width=0),
                    fillcolor='rgba(119, 221, 119, 0.4)', layer='below')
        # --- Rectángulo para la compresión zona C
        fig.add_shape(type="rect", x0=END_TIME, x1=limit_time, y0=y1_value-(zona*3), y1=y1_value-(zona*2),
                    xref='x', yref='y1', line=dict(color='green', width=0),
                    fillcolor='rgba(119, 221, 119, 0.6)', layer='below')
    # Zonas para Short (rojo pastel, de más transparente abajo a más opaco arriba)
    elif entry_type == 'Short':
        fig.add_shape(type="rect", x0=END_TIME, x1=limit_time, y0=y0_value, y1=y0_value+zona,
                    xref='x', yref='y1', line=dict(color='red', width=0),
                    fillcolor='rgba(252, 120, 120, 0.2)', layer='below')
        fig.add_shape(type="rect", x0=END_TIME, x1=limit_time, y0=y0_value+zona, y1=y0_value+(zona*2),
                    xref='x', yref='y1', line=dict(color='red', width=0),
                    fillcolor='rgba(252, 120, 120, 0.4)', layer='below')
        fig.add_shape(type="rect", x0=END_TIME, x1=limit_time, y0=y0_value+(zona*2), y1=y0_value+(zona*3),
                    xref='x', yref='y1', line=dict(color='red', width=0),
                    fillcolor='rgba(252, 120, 120, 0.6)', layer='below')



    # --- Vertical lines
    
    fig.add_shape(type="line", x0=START_TIME, x1=START_TIME, y0=0, y1=1, xref="x", yref="paper", line=dict(color="blue", width=1), opacity=0.5)
    fig.add_shape(type="line", x0=END_TIME, x1=END_TIME, y0=0, y1=1, xref="x", yref="paper", line=dict(color="grey", width=1), opacity=0.5)
    fig.add_shape(type="line", x0=too_late_patito_negro, x1=too_late_patito_negro, y0=0, y1=1, xref="x", yref="paper", line=dict(color="grey", width=1), opacity=0.5)
    fig.add_shape(type="line", x0=START_TIME, x1=START_TIME, y0=0, y1=1, xref="x", yref="paper", line=dict(color="blue", width=1), opacity=0.5)
    fig.add_shape(type="line", x0=limit_time, x1=limit_time, y0=0, y1=1, xref="x", yref="paper", line=dict(color="grey", width=1), opacity=0.5)  

    # --- Horizontal reference lines
    fig.add_shape(type="line", x0=END_TIME, x1=too_late_patito_negro, y0=midpoint, y1=midpoint, xref="x", yref="y1", line=dict(color="grey", width=1,dash="dot"), opacity=0.6) 
    fig.add_shape(type="line", x0=END_TIME, x1=too_late_patito_negro, y0=y1_value, y1=y1_value, xref="x", yref="y1", line=dict(color="blue", width=1), opacity=0.7)  
    fig.add_shape(type="line", x0=END_TIME, x1=too_late_patito_negro, y0=y0_value, y1=y0_value, xref="x", yref="y1", line=dict(color="blue", width=1), opacity=0.7)  
    fig.add_shape(type="line", x0=END_TIME, x1=too_late_patito_negro, y0=y1_subvalue, y1=y1_subvalue, xref="x", yref="y1", line=dict(color="blue", width=1, dash="dot"), opacity=0.7)  
  
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

    # --- Entry/Exit Orders and lines
    if df_orders is not None and not df_orders.empty:
        # Triángulo verde para entrada long, rojo para short
        for _, row in df_orders.iterrows():
            # Entrada
            if pd.notnull(row['entry_time']) and pd.notnull(row['entry_price']):
                color = 'limegreen' if row['entry_type'] == 'Long' else 'red'
                symbol = 'triangle-up' if row['entry_type'] == 'Long' else 'triangle-down'
                fig.add_trace(go.Scatter(
                    x=[row['entry_time']],
                    y=[row['entry_price']],
                    mode='markers',
                    marker=dict(color=color, size=18, symbol=symbol),
                    name='Entry'
                ), row=1, col=1)

            # Salida
            if pd.notnull(row['exit_time']) and pd.notnull(row['exit_price']):
                fig.add_trace(go.Scatter(
                    x=[row['exit_time']],
                    y=[row['exit_price']],
                    mode='markers',
                    marker=dict(color='black', size=14, symbol='x'),
                    name='Exit'
                ), row=1, col=1)

            # Línea de entrada a salida
            if pd.notnull(row['entry_time']) and pd.notnull(row['entry_price']) and pd.notnull(row['exit_time']) and pd.notnull(row['exit_price']):
                fig.add_trace(go.Scatter(
                    x=[row['entry_time'], row['exit_time']],
                    y=[row['entry_price'], row['exit_price']],
                    mode='lines',
                    line=dict(color='gray', width=1, dash='dot'),
                    name='Entry to Exit'
                ), row=1, col=1)

    fig.update_layout(
        dragmode='pan',
        title=titulo,
        xaxis=dict(showgrid=False, showline=True, linewidth=1, linecolor='lightgrey', mirror=True),
        yaxis=dict(title="Precio", showgrid=False, showline=True, linewidth=1, linecolor='lightgrey', mirror=True),
        xaxis2=dict(showgrid=False, showline=True, linewidth=1, linecolor='lightgrey', mirror=False),
        yaxis2=dict(title="", showgrid=False, showline=True, linewidth=1, linecolor='lightgrey', mirror=True),
        xaxis_rangeslider_visible=False,
        width=1500,
        height=int(1400 * 0.6),
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
    #webbrowser.open('file://' + os.path.realpath(output_file))         # INDICAR QUE SE ABRA EL NAVEGADOR AUTOMÁTICAMENTE O COMENTAR  PARA NO SATURAR LA KERNEL
    
