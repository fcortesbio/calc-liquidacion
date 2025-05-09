import pandas as pd
from datetime import datetime, timedelta

# ============================
# 1. CONFIGURACIÓN GENERAL
# ============================

fecha_inicio_contrato = datetime(2023, 4, 17)
fecha_fin_contrato = datetime(2024, 2, 17)
fecha_actual = datetime(2025, 5, 9)

salario_base = 2_100_000
salario_diario = salario_base / 30

# ============================
# 2. CARGA Y PREPROCESAMIENTO DE DATOS
# ============================

# Carga el archivo CSV con la información de los desprendibles de nómina
df_paystubs = pd.read_csv('paystubs-summary.csv')

# Convierte fechas y extrae metadatos útiles
df_paystubs['Period_Start_Date'] = pd.to_datetime(df_paystubs['pay_period_starts'])
df_paystubs['Period_End_Date'] = pd.to_datetime(df_paystubs['pay_period_ends'])
df_paystubs['year_month_period'] = df_paystubs['Period_Start_Date'].dt.to_period('M')

# Columnas relevantes para el cálculo de extras
extras_cols = ['sunday_bonus', 'holiday_bonus', 'night_bonus', 'day_overtime', 'night_overtime']

for col in extras_cols + ['base_salary', 'aux_transp']:
    df_paystubs[col] = pd.to_numeric(df_paystubs[col], errors='coerce').fillna(0).astype(int)

df_paystubs['total_extras'] = df_paystubs[extras_cols].sum(axis=1)

# ============================
# 3. FUNCIONES AUXILIARES
# ============================

def calcular_dias_laborados(inicio, fin):
    return max((fin - inicio).days + 1, 0)

def get_proportional_earnings_for_period(df, start, end):
    total_base, total_extras, total_aux = 0, 0, 0
    dias_periodo = calcular_dias_laborados(start, end)

    for _, row in df.iterrows():
        ps_start, ps_end = row['Period_Start_Date'], row['Period_End_Date']
        overlap_start, overlap_end = max(start, ps_start), min(end, ps_end)

        if overlap_start <= overlap_end:
            overlap_days = calcular_dias_laborados(overlap_start, overlap_end)
            pay_period_days = calcular_dias_laborados(ps_start, ps_end)
            if pay_period_days == 0:
                continue
            ratio = overlap_days / pay_period_days
            total_base += row['base_salary'] * ratio
            total_extras += row['total_extras'] * ratio
            total_aux += row['aux_transp'] * ratio

    if dias_periodo == 0:
        return {"avg_monthly_salary": 0, "avg_monthly_aux": 0, "avg_base_only": 0, "days": 0}

    return {
        "avg_monthly_salary": (total_base + total_extras) / dias_periodo * 30,
        "avg_monthly_aux": total_aux / dias_periodo * 30,
        "avg_base_only": total_base / dias_periodo * 30,
        "days": dias_periodo,
    }

# ============================
# 4. CALCULO DE PRESTACIONES
# ============================

# Rango de fechas por prestación
prima_periods = [
    (datetime(2023, 4, 17), datetime(2023, 6, 30)),
    (datetime(2023, 7, 1), datetime(2023, 12, 31)),
    (datetime(2024, 1, 1), fecha_fin_contrato)
]

cesantias_periods = [
    (datetime(2023, 4, 17), datetime(2023, 12, 31)),
    (datetime(2024, 1, 1), fecha_fin_contrato)
]

vacaciones_period = (fecha_inicio_contrato, fecha_fin_contrato)

# Calcular primas
primas = []
for inicio, fin in prima_periods:
    data = get_proportional_earnings_for_period(df_paystubs, inicio, fin)
    valor = (data['avg_monthly_salary'] + data['avg_monthly_aux']) * data['days'] / 360
    primas.append(round(valor))

# Calcular cesantías e intereses
cesantias = []
intereses = []
for inicio, fin in cesantias_periods:
    data = get_proportional_earnings_for_period(df_paystubs, inicio, fin)
    ces = (data['avg_monthly_salary'] + data['avg_monthly_aux']) * data['days'] / 360
    int_ces = ces * data['days'] * 0.12 / 360
    cesantias.append(round(ces))
    intereses.append(round(int_ces))

# Calcular vacaciones
vac_data = get_proportional_earnings_for_period(df_paystubs, *vacaciones_period)
vacaciones = round(vac_data['avg_base_only'] * vac_data['days'] / 720)

# ============================
# 5. INDEMNIZACIONES Y SANCIONES
# ============================

fecha_limite_pago = fecha_fin_contrato + timedelta(days=15)
dias_mora_liquidacion = max((fecha_actual - fecha_limite_pago).days, 0)
indem_mora_liquidacion = round(salario_diario * dias_mora_liquidacion)

fecha_limite_cesantias = datetime(2024, 2, 15)
dias_mora_cesantias = max((fecha_actual - fecha_limite_cesantias).days, 0)
sancion_cesantias = round(salario_diario * dias_mora_cesantias)

dias_servicio = calcular_dias_laborados(fecha_inicio_contrato, fecha_fin_contrato)
indem_despido = round(salario_base / 360 * dias_servicio)

# ============================
# 6. RESUMEN FINAL
# ============================

pretensiones = sum(primas[2:]) + sum(cesantias) + sum(intereses) + vacaciones
indemnizaciones = indem_mora_liquidacion + sancion_cesantias + indem_despido

monto_total = pretensiones + indemnizaciones

print("--- RESUMEN DE LIQUIDACIÓN ---")
print(f"Prima proporcional 2024: ${primas[2]}")
print(f"Cesantías: ${sum(cesantias)}")
print(f"Intereses sobre cesantías: ${sum(intereses)}")
print(f"Vacaciones: ${vacaciones}")
print(f"Indemnización mora liquidación: ${indem_mora_liquidacion}")
print(f"Sanción mora cesantías: ${sancion_cesantias}")
print(f"Indemnización por despido: ${indem_despido}")
print(f"TOTAL PRETENSIONES: ${monto_total}")
