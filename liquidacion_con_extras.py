
from datetime import datetime
import pandas as pd

# === CONFIGURABLE VARIABLES ===
# Base salary and auxilio values
salario_base_2023 = 2_100_000
aux_transporte_2023 = 140_606
salario_base_2024 = 2_100_000
aux_transporte_2024 = 162_000

# Extras (recargos, dominicales, festivos, etc.) for 2023 as estimated
extras_total_2023 = 1_861_430  # Total extra income reported in paystubs
meses_laborados_2023 = 8.5
salario_promedio_2023 = salario_base_2023 + (extras_total_2023 / meses_laborados_2023)

# 2024 will not include extras for now
salario_promedio_2024 = salario_base_2024

# Work periods
fecha_inicio_2023 = datetime(2023, 4, 17)
fecha_fin_2023 = datetime(2023, 12, 31)

fecha_inicio_2024 = datetime(2024, 1, 1)
fecha_fin_2024 = datetime(2024, 2, 17)

fecha_limite_cesantias = datetime(2024, 2, 14)
fecha_actual = datetime.now()

# === FUNCTION DEFINITIONS ===

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
dias_2023 = calcular_dias_laborados(fecha_inicio_2023, fecha_fin_2023)
dias_2024 = calcular_dias_laborados(fecha_inicio_2024, fecha_fin_2024)

# Cesantías
cesantias_2023 = calcular_cesantias(dias_2023, salario_promedio_2023, aux_transporte_2023)
cesantias_2024 = calcular_cesantias(dias_2024, salario_promedio_2024, aux_transporte_2024)

# Prima de Servicios
prima_2023 = calcular_prima(dias_2023, salario_promedio_2023, aux_transporte_2023)
prima_2024 = calcular_prima(dias_2024, salario_promedio_2024, aux_transporte_2024)

# Vacaciones
vacaciones_2023 = calcular_vacaciones(dias_2023, salario_promedio_2023)
vacaciones_2024 = calcular_vacaciones(dias_2024, salario_promedio_2024)

# Intereses sobre cesantías
intereses_2023 = calcular_intereses_cesantias(cesantias_2023, dias_2023)
intereses_2024 = calcular_intereses_cesantias(cesantias_2024, dias_2024)

# Moratoria por cesantías no consignadas después del 14 de febrero 2024
dias_mora_cesantias = calcular_diferencia_dias(fecha_limite_cesantias, fecha_actual)
moratoria_cesantias = calcular_moratoria(salario_base_2024 / 30, dias_mora_cesantias)

# Output all results
results = pd.DataFrame({
    "Concepto": [
        "Días laborados 2023", "Días laborados 2024",
        "Cesantías 2023 (con extras)", "Cesantías 2024",
        "Prima 2023 (con extras)", "Prima 2024",
        "Vacaciones 2023 (con extras)", "Vacaciones 2024",
        "Intereses Cesantías 2023", "Intereses Cesantías 2024",
        "Días de mora Cesantías", "Moratoria Cesantías"
    ],
    "Valor": [
        dias_2023, dias_2024,
        round(cesantias_2023, 2), round(cesantias_2024, 2),
        round(prima_2023, 2), round(prima_2024, 2),
        round(vacaciones_2023, 2), round(vacaciones_2024, 2),
        round(intereses_2023, 2), round(intereses_2024, 2),
        dias_mora_cesantias, round(moratoria_cesantias, 2)
    ]
})

print("\n--- LIQUIDACIÓN DETALLADA ---")
print(results.to_string(index=False))
