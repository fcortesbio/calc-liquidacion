
from datetime import datetime
import pandas as pd

# === CONFIGURABLE VARIABLES ===
salario_base_2023 = 2_100_000
aux_transporte_2023 = 140_606
salario_base_2024 = 2_100_000
aux_transporte_2024 = 162_000

# Extras (recargos, dominicales, festivos, etc.) for 2023 as estimated
extras_total_2023 = 1_861_430
meses_laborados_2023 = 8.5
salario_promedio_2023 = salario_base_2023 + (extras_total_2023 / meses_laborados_2023)
salario_promedio_2024 = salario_base_2024

# Work periods
fecha_inicio_abr = datetime(2023, 4, 17)
fecha_fin_jun = datetime(2023, 6, 30)
fecha_inicio_jul = datetime(2023, 7, 1)
fecha_fin_dic = datetime(2023, 12, 31)
fecha_inicio_ene = datetime(2024, 1, 1)
fecha_fin_feb = datetime(2024, 2, 17)

fecha_limite_cesantias = datetime(2024, 2, 14)
fecha_limite_prima = datetime(2024, 3, 13)
fecha_actual = datetime.now()

# === FUNCTIONS ===
def calcular_dias_laborados(inicio, fin):
    return (fin - inicio).days + 1

def calcular_diferencia_dias(fecha_inicio, fecha_fin):
    return (fecha_fin - fecha_inicio).days

def calcular_cesantias(dias, salario, aux):
    return ((salario + aux) * dias) / 360

def calcular_prima(dias, salario, aux):
    return ((salario + aux) * dias) / 360

def calcular_vacaciones(dias, salario):
    return (salario * dias) / 720

def calcular_intereses_cesantias(cesantias, dias):
    return (cesantias * dias * 0.12) / 360

def calcular_moratoria(dia_salario, dias_mora):
    return dia_salario * dias_mora

# === CALCULATIONS ===
# Days
dias_abr_jun = calcular_dias_laborados(fecha_inicio_abr, fecha_fin_jun)
dias_jul_dic = calcular_dias_laborados(fecha_inicio_jul, fecha_fin_dic)
dias_ene_feb = calcular_dias_laborados(fecha_inicio_ene, fecha_fin_feb)
dias_2023 = dias_abr_jun + dias_jul_dic
dias_2024 = dias_ene_feb

# Prima splits
prima_abr_jun = calcular_prima(dias_abr_jun, salario_promedio_2023, aux_transporte_2023)
prima_jul_dic = calcular_prima(dias_jul_dic, salario_promedio_2023, aux_transporte_2023)
prima_ene_feb = calcular_prima(dias_ene_feb, salario_promedio_2024, aux_transporte_2024)

# Cesantías
cesantias_2023 = calcular_cesantias(dias_2023, salario_promedio_2023, aux_transporte_2023)
cesantias_2024 = calcular_cesantias(dias_2024, salario_promedio_2024, aux_transporte_2024)

# Vacaciones
vacaciones_2023 = calcular_vacaciones(dias_2023, salario_promedio_2023)
vacaciones_2024 = calcular_vacaciones(dias_2024, salario_promedio_2024)

# Intereses sobre cesantías
intereses_2023 = calcular_intereses_cesantias(cesantias_2023, dias_2023)
intereses_2024 = calcular_intereses_cesantias(cesantias_2024, dias_2024)

# Moratorias
dias_mora_cesantias = calcular_diferencia_dias(fecha_limite_cesantias, fecha_actual)
dias_mora_prima = calcular_diferencia_dias(fecha_limite_prima, fecha_actual)
moratoria_cesantias = calcular_moratoria(salario_base_2024 / 30, dias_mora_cesantias)
moratoria_prima = calcular_moratoria(salario_base_2024 / 30, dias_mora_prima)

# === OUTPUT ===
results = pd.DataFrame({
    "Concepto": [
        "Días laborados 2023", "Días laborados 2024",
        "Prima Abr-Jun 2023", "Prima Jul-Dic 2023", "Prima Ene-Feb 2024",
        "Cesantías 2023 (con extras)", "Cesantías 2024",
        "Vacaciones 2023 (con extras)", "Vacaciones 2024",
        "Intereses Cesantías 2023", "Intereses Cesantías 2024",
        "Días de mora Cesantías", "Moratoria Cesantías",
        "Días de mora Prima", "Moratoria Prima"
    ],
    "Valor": [
        dias_2023, dias_2024,
        round(prima_abr_jun, 2), round(prima_jul_dic, 2), round(prima_ene_feb, 2),
        round(cesantias_2023, 2), round(cesantias_2024, 2),
        round(vacaciones_2023, 2), round(vacaciones_2024, 2),
        round(intereses_2023, 2), round(intereses_2024, 2),
        dias_mora_cesantias, round(moratoria_cesantias, 2),
        dias_mora_prima, round(moratoria_prima, 2)
    ]
})

print("\n--- LIQUIDACIÓN DETALLADA ---")
print(results.to_string(index=False))
