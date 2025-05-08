
from datetime import datetime

# === CONFIGURABLE VARIABLES ===
salario_2023 = 2_100_000
aux_transporte_2023 = 140_606

salario_2024 = 2_100_000
aux_transporte_2024 = 162_000

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
cesantias_2023 = calcular_cesantias(dias_2023, salario_2023, aux_transporte_2023)
cesantias_2024 = calcular_cesantias(dias_2024, salario_2024, aux_transporte_2024)

# Prima de Servicios
prima_2023 = calcular_prima(dias_2023, salario_2023, aux_transporte_2023)
prima_2024 = calcular_prima(dias_2024, salario_2024, aux_transporte_2024)

# Vacaciones
vacaciones_2023 = calcular_vacaciones(dias_2023, salario_2023)
vacaciones_2024 = calcular_vacaciones(dias_2024, salario_2024)

# Intereses sobre cesantías
intereses_2023 = calcular_intereses_cesantias(cesantias_2023, dias_2023)
intereses_2024 = calcular_intereses_cesantias(cesantias_2024, dias_2024)

# Moratoria por intereses de prima 

# Moratoria por cesantías no consignadas después del 14 de febrero 2024
dias_mora_cesantias = calcular_diferencia_dias(fecha_limite_cesantias, fecha_actual)
moratoria_cesantias = calcular_moratoria(salario_2024 / 30, dias_mora_cesantias)

# === DISPLAY RESULTS ===
print("\n--- LIQUIDACIÓN DETALLADA ---")
print(f"Días laborados 2023: {dias_2023}")
print(f"Días laborados 2024: {dias_2024}")
print(f"Cesantías 2023: ${cesantias_2023:,.2f}")
print(f"Cesantías 2024: ${cesantias_2024:,.2f}")
print(f"Prima de Servicios 2023: ${prima_2023:,.2f}")
print(f"Prima de Servicios 2024: ${prima_2024:,.2f}")
print(f"Vacaciones 2023: ${vacaciones_2023:,.2f}")
print(f"Vacaciones 2024: ${vacaciones_2024:,.2f}")
print(f"Intereses sobre Cesantías 2023: ${intereses_2023:,.2f}")
print(f"Intereses sobre Cesantías 2024: ${intereses_2024:,.2f}")
print(f"Días de mora en pago de cesantías (desde 14/feb/2024): {dias_mora_cesantias}")
print(f"Valor de sanción moratoria por cesantías: ${moratoria_cesantias:,.2f}")


# --- LIQUIDACIÓN DETALLADA ---
# Días laborados 2023: 259
# Días laborados 2024: 48
# Cesantías 2023: $1,611,991.54
# Cesantías 2024: $301,600.00
# Prima de Servicios 2023: $1,611,991.54
# Prima de Servicios 2024: $301,600.00
# Vacaciones 2023: $755,416.67
# Vacaciones 2024: $140,000.00
# Intereses sobre Cesantías 2023: $139,168.60
# Intereses sobre Cesantías 2024: $4,825.60
# Días de mora en pago de cesantías (desde 14/feb/2024): 448
# Valor de sanción moratoria por cesantías: $31,360,000.00
