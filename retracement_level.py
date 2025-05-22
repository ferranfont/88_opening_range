import pandas as pd
import matplotlib.pyplot as plt

# Lee el fichero directamente
df = pd.read_csv('outputs/summary_by_retracement_only.csv')

# Filtra solo los retracement_level <= 0.01
df = df[df['retracement_level'] <= 0.01]

# Elimina filas donde no hay datos de sum_profit_usd
df = df.dropna(subset=['sum_profit_usd'])

# Crea el gráfico de barras
plt.figure(figsize=(10,6))
plt.bar(df['retracement_level'], df['sum_profit_usd'], width=0.0007, align='center', edgecolor='k')

plt.xlabel('Retracement Level')
plt.ylabel('Sum Profit (USD)')
plt.title('Distribución de Sum Profit USD por Retracement Level')
plt.grid(axis='y', linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()
