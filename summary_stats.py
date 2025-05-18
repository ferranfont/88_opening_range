import pandas as pd

# Leer CSV
df = pd.read_csv('outputs/summary_stats.csv')
df.columns = df.columns.str.strip()

# Convertir a booleanos reales
df['stop_out_outside_range'] = df['stop_out_outside_range'].astype(str).str.strip().map({'True': True, 'False': False})

# Contar total de filas
total = len(df)

# Contar True y False
count_true = (df['stop_out_outside_range'] == True).sum()
count_false = (df['stop_out_outside_range'] == False).sum()

# Calcular porcentajes
pct_true = (count_true / total) * 100
pct_false = (count_false / total) * 100

# Mostrar resultados
print(f"✅ True  ➜ {count_true} filas ({pct_true:.2f}%)")
print(f"✅ False ➜ {count_false} filas ({pct_false:.2f}%)")
print(f"🧾 Total ➜ {total} filas analizadas")
