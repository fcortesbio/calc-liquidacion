import pandas as pd
from datetime import datetime, timedelta

# ============================
# 1. CONFIGURACIÓN GENERAL Y CONSTANTES
# ============================
# --- Fechas Clave del Contrato y Cálculo ---
FECHA_INICIO_CONTRATO = datetime(2023, 4, 17)
FECHA_FIN_CONTRATO = datetime(2024, 2, 17)
FECHA_ACTUAL_CALCULO = datetime(2025, 5, 9) # Fecha en que se realizan estos cálculos

# --- Salario Base de Referencia ---
# Este es el salario base contractual. Se usa como referencia y para cálculos
# donde no se requiere promedio de devengos variables (ej. indemnización por despido).
SALARIO_BASE_CONTRACTUAL = 2_100_000
SALARIO_DIARIO_CONTRACTUAL = SALARIO_BASE_CONTRACTUAL / 30 # Para cálculos basados en 30 días por mes

# --- Periodos para Cálculo de Prestaciones Sociales ---
# Prima de Servicios
FECHA_INICIO_PRIMA1_2023 = datetime(2023, 4, 17)
FECHA_FIN_PRIMA1_2023 = datetime(2023, 6, 30)
FECHA_INICIO_PRIMA2_2023 = datetime(2023, 7, 1)
FECHA_FIN_PRIMA2_2023 = datetime(2023, 12, 31)
FECHA_INICIO_PRIMA_2024 = datetime(2024, 1, 1)
FECHA_FIN_PRIMA_2024 = FECHA_FIN_CONTRATO # Proporcional hasta fin de contrato

# Cesantías e Intereses sobre Cesantías
FECHA_INICIO_CESANTIAS_2023 = datetime(2023, 4, 17)
FECHA_FIN_CESANTIAS_2023 = datetime(2023, 12, 31)
FECHA_INICIO_CESANTIAS_2024 = datetime(2024, 1, 1)
FECHA_FIN_CESANTIAS_2024 = FECHA_FIN_CONTRATO # Proporcional hasta fin de contrato

# Vacaciones
FECHA_INICIO_VACACIONES = FECHA_INICIO_CONTRATO
FECHA_FIN_VACACIONES = FECHA_FIN_CONTRATO

# --- Archivo de Datos ---
PAYSTUBS_CSV_FILE = 'paystubs-summary.csv'

# ============================
# 2. FUNCIONES AUXILIARES
# ============================

def calcular_dias_laborados(fecha_inicio, fecha_fin):
    """
    Calcula el número de días laborados entre dos fechas (inclusive).
    Se asume que un mes tiene 30 días para efectos de liquidación laboral si es necesario,
    pero aquí contamos días calendario exactos para periodos.
    """
    if not isinstance(fecha_inicio, datetime) or not isinstance(fecha_fin, datetime):
        raise TypeError("Las fechas de inicio y fin deben ser objetos datetime.")
    if fecha_inicio > fecha_fin:
        return 0
    return (fecha_fin - fecha_inicio).days + 1

def get_proportional_earnings_for_period(df_paystubs, period_start_date, period_end_date):
    """
    Calcula el salario base, extras y auxilio de transporte proporcionales devengados
    dentro de un periodo específico, basado en los desprendibles de nómina.
    Estos valores se usan para calcular el promedio mensual para las fórmulas de liquidación.
    """
    total_pro_rata_base_salary = 0.0
    total_pro_rata_extras = 0.0
    total_pro_rata_aux_transp = 0.0

    num_days_in_calc_period = calcular_dias_laborados(period_start_date, period_end_date)

    if num_days_in_calc_period == 0:
        return {
            "avg_monthly_salary_for_formula": 0.0,
            "avg_monthly_aux_for_formula": 0.0,
            "avg_monthly_base_salary_only_for_formula": 0.0,
            "worked_days_in_period": 0,
        }

    for _, row in df_paystubs.iterrows():
        paystub_period_start = row['Period_Start_Date']
        paystub_period_end = row['Period_End_Date']

        # Calcular la intersección (solapamiento) entre el periodo de pago del desprendible y el periodo de cálculo
        overlap_start = max(period_start_date, paystub_period_start)
        overlap_end = min(period_end_date, paystub_period_end)

        if overlap_start <= overlap_end:
            overlap_days = calcular_dias_laborados(overlap_start, overlap_end)
            days_in_paystub_period = calcular_dias_laborados(paystub_period_start, paystub_period_end)

            if days_in_paystub_period == 0: # Evitar división por cero si el periodo del desprendible es inválido
                continue

            # Proporción del desprendible que cae dentro del periodo de cálculo
            ratio = overlap_days / days_in_paystub_period

            total_pro_rata_base_salary += row['base_salary'] * ratio
            total_pro_rata_extras += row['total_extras'] * ratio
            total_pro_rata_aux_transp += row['aux_transp'] * ratio

    # Calcular promedios mensuales basados en los devengos proporcionales y los días del periodo de cálculo
    # Se multiplica por 30 para obtener un promedio mensual estándar para las fórmulas laborales.
    avg_monthly_salary_for_formula = \
        (total_pro_rata_base_salary + total_pro_rata_extras) / num_days_in_calc_period * 30
    avg_monthly_aux_for_formula = \
        total_pro_rata_aux_transp / num_days_in_calc_period * 30
    avg_monthly_base_salary_only_for_formula = \
        total_pro_rata_base_salary / num_days_in_calc_period * 30

    return {
        "avg_monthly_salary_for_formula": avg_monthly_salary_for_formula,
        "avg_monthly_aux_for_formula": avg_monthly_aux_for_formula,
        "avg_monthly_base_salary_only_for_formula": avg_monthly_base_salary_only_for_formula,
        "worked_days_in_period": num_days_in_calc_period,
    }

# ============================
# 3. CARGA Y PREPROCESAMIENTO DE DATOS DE DESPRENDIBLES DE NÓMINA
# ============================
try:
    df_paystubs = pd.read_csv(PAYSTUBS_CSV_FILE)
except FileNotFoundError:
    print(f"Error: El archivo '{PAYSTUBS_CSV_FILE}' no fue encontrado. Por favor, verifique la ruta.")
    exit()

# Convertir columnas de fecha a datetime
# Asumimos que 'pay_period_starts' y 'pay_period_ends' son los nombres en el CSV.
df_paystubs['Period_Start_Date'] = pd.to_datetime(df_paystubs['pay_period_starts'], errors='coerce')
df_paystubs['Period_End_Date'] = pd.to_datetime(df_paystubs['pay_period_ends'], errors='coerce')

# Validar que las fechas se hayan convertido correctamente
if df_paystubs['Period_Start_Date'].isnull().any() or df_paystubs['Period_End_Date'].isnull().any():
    print("Advertencia: Algunas fechas en 'pay_period_starts' o 'pay_period_ends' no pudieron ser convertidas.")
    # Podrías optar por eliminar filas con NaT o manejarlo de otra forma
    df_paystubs.dropna(subset=['Period_Start_Date', 'Period_End_Date'], inplace=True)


# Extraer año y mes para análisis mensual
df_paystubs['year_month_period'] = df_paystubs['Period_Start_Date'].dt.to_period('M')

# Columnas de ingresos adicionales (extras)
extras_cols = ['sunday_bonus', 'holiday_bonus', 'night_bonus', 'day_overtime', 'night_overtime']
numeric_cols_to_process = extras_cols + ['base_salary', 'aux_transp']

# Asegurar que las columnas numéricas sean tratadas como números y rellenar NaN con 0
for col in numeric_cols_to_process:
    if col in df_paystubs.columns:
        df_paystubs[col] = pd.to_numeric(df_paystubs[col], errors='coerce').fillna(0).astype(int)
    else:
        print(f"Advertencia: La columna '{col}' no se encuentra en el CSV. Se asumirá como 0.")
        df_paystubs[col] = 0 # Crear la columna con ceros si no existe

# Calcular el total de extras
df_paystubs['total_extras'] = df_paystubs[extras_cols].sum(axis=1)


# --- 3.1 Resumen Financiero Mensual (Periodo del Contrato) ---
monthly_summary_list = []
# Agrupar por mes para calcular totales mensuales
for month_period, group in df_paystubs.groupby('year_month_period'):
    monthly_base_salary = group['base_salary'].sum()
    monthly_extras = group['total_extras'].sum()
    monthly_salary_total = monthly_base_salary + monthly_extras # Salario mensual = Salario base + Extras
    monthly_aux_transporte = group['aux_transp'].sum()

    # Ingreso Base de Cotización (IBC) para seguridad social (pensión, salud)
    # Generalmente es Salario Total + Auxilio de Transporte (si aplica)
    monthly_ibc = monthly_salary_total + monthly_aux_transporte
    # Aporte a Pensión (asumiendo 16% total, 12% empleador, 4% empleado. Aquí se muestra el 12% como referencia del costo para empleador)
    # O el 12% se refiere al aporte del empleador a un fondo de pensiones específico. Clarificar si es necesario.
    # El script original indicaba "12% es la suma del aporte del empleador y el empleado", lo cual es incorrecto.
    # El aporte total a pensión es 16% (12% empleador, 4% empleado).
    # Si se quiere mostrar el aporte total, sería 0.16. Si es solo el del empleador, 0.12.
    # Mantendré el 0.12 como en el original, pero con esta nota.
    monthly_aporte_pension_empleador = monthly_ibc * 0.12 # Ajustar si es el total (0.16)

    monthly_summary_list.append({
        "Mes": month_period.strftime('%Y-%m'),
        "Salario Base": monthly_base_salary,
        "Extras": monthly_extras,
        "Salario Total (Base + Extras)": monthly_salary_total,
        "Auxilio Transporte": monthly_aux_transporte,
        "IBC (Ingreso Base Cotización)": monthly_ibc,
        "Aporte Pensión Referencia (12%)": round(monthly_aporte_pension_empleador) # Redondeo
    })

df_monthly_report = pd.DataFrame(monthly_summary_list)

# Filtrar el reporte para el periodo de interés del contrato
contract_start_period = FECHA_INICIO_CONTRATO.to_period('M')
contract_end_period = FECHA_FIN_CONTRATO.to_period('M')
df_monthly_report['Month_Period_Obj'] = pd.PeriodIndex(df_monthly_report['Mes'], freq='M')

df_monthly_report_filtered = df_monthly_report[
    (df_monthly_report['Month_Period_Obj'] >= contract_start_period) &
    (df_monthly_report['Month_Period_Obj'] <= contract_end_period)
].drop(columns=['Month_Period_Obj'])

print("--- RESUMEN FINANCIERO MENSUAL (Periodo del Contrato) ---")
print(df_monthly_report_filtered.to_string(index=False))
print("\n")


# ============================
# 4. CÁLCULO DE PRESTACIONES DE LIQUIDACIÓN
# ============================
# Las fórmulas usan una base de 360 días al año.

# --- 4.1 Prima de Servicios ---
# Fórmula: (Salario promedio mensual + Auxilio de transporte promedio mensual) * Días trabajados en el semestre / 360
base_prima1_2023_calc = get_proportional_earnings_for_period(df_paystubs, FECHA_INICIO_PRIMA1_2023, FECHA_FIN_PRIMA1_2023)
prima_1_2023 = (base_prima1_2023_calc['avg_monthly_salary_for_formula'] +
                base_prima1_2023_calc['avg_monthly_aux_for_formula']) * base_prima1_2023_calc['worked_days_in_period'] / 360

base_prima2_2023_calc = get_proportional_earnings_for_period(df_paystubs, FECHA_INICIO_PRIMA2_2023, FECHA_FIN_PRIMA2_2023)
prima_2_2023 = (base_prima2_2023_calc['avg_monthly_salary_for_formula'] +
                base_prima2_2023_calc['avg_monthly_aux_for_formula']) * base_prima2_2023_calc['worked_days_in_period'] / 360

base_prima_2024_calc = get_proportional_earnings_for_period(df_paystubs, FECHA_INICIO_PRIMA_2024, FECHA_FIN_PRIMA_2024)
prima_2024_proporcional = (base_prima_2024_calc['avg_monthly_salary_for_formula'] +
                           base_prima_2024_calc['avg_monthly_aux_for_formula']) * base_prima_2024_calc['worked_days_in_period'] / 360

# --- 4.2 Cesantías ---
# Fórmula: (Salario promedio mensual + Auxilio de transporte promedio mensual) * Días trabajados en el periodo / 360
base_cesantias_2023_calc = get_proportional_earnings_for_period(df_paystubs, FECHA_INICIO_CESANTIAS_2023, FECHA_FIN_CESANTIAS_2023)
cesantias_2023 = (base_cesantias_2023_calc['avg_monthly_salary_for_formula'] +
                  base_cesantias_2023_calc['avg_monthly_aux_for_formula']) * base_cesantias_2023_calc['worked_days_in_period'] / 360

base_cesantias_2024_calc = get_proportional_earnings_for_period(df_paystubs, FECHA_INICIO_CESANTIAS_2024, FECHA_FIN_CESANTIAS_2024)
cesantias_2024_proporcional = (base_cesantias_2024_calc['avg_monthly_salary_for_formula'] +
                               base_cesantias_2024_calc['avg_monthly_aux_for_formula']) * base_cesantias_2024_calc['worked_days_in_period'] / 360

# --- 4.3 Intereses sobre las Cesantías ---
# Fórmula: (Valor Cesantías * Días trabajados en el periodo * 0.12) / 360
intereses_cesantias_2023 = (cesantias_2023 * base_cesantias_2023_calc['worked_days_in_period'] * 0.12) / 360
intereses_cesantias_2024_proporcional = (cesantias_2024_proporcional * base_cesantias_2024_calc['worked_days_in_period'] * 0.12) / 360

# --- 4.4 Vacaciones ---
# Fórmula: (Salario base promedio mensual (sin extras ni auxilio transp.) * Días trabajados en el periodo) / 720
# (Se pagan 15 días hábiles de salario por año trabajado, lo que equivale a Salario_Mensual / 2)
base_vacaciones_calc = get_proportional_earnings_for_period(df_paystubs, FECHA_INICIO_VACACIONES, FECHA_FIN_VACACIONES)
vacaciones_compensadas = (base_vacaciones_calc['avg_monthly_base_salary_only_for_formula'] *
                          base_vacaciones_calc['worked_days_in_period']) / 720

# --- 4.5 Reporte de Liquidación ---
liquidacion_items = [
    {"Concepto": f"Prima 1er Semestre 2023 ({FECHA_INICIO_PRIMA1_2023.strftime('%b %d')} - {FECHA_FIN_PRIMA1_2023.strftime('%b %d')})", "Valor": prima_1_2023, "Estado": "Pagada"}, # Asumiendo pagada según original
    {"Concepto": f"Prima 2do Semestre 2023 ({FECHA_INICIO_PRIMA2_2023.strftime('%b %d')} - {FECHA_FIN_PRIMA2_2023.strftime('%b %d')})", "Valor": prima_2_2023, "Estado": "Pagada"}, # Asumiendo pagada según original
    {"Concepto": f"Prima Proporcional 2024 ({FECHA_INICIO_PRIMA_2024.strftime('%b %d')} - {FECHA_FIN_PRIMA_2024.strftime('%b %d')})", "Valor": prima_2024_proporcional, "Estado": "No Pagada"},
    {"Concepto": f"Cesantías 2023 ({FECHA_INICIO_CESANTIAS_2023.strftime('%b %d')} - {FECHA_FIN_CESANTIAS_2023.strftime('%b %d')})", "Valor": cesantias_2023, "Estado": "No Pagada"},
    {"Concepto": "Intereses sobre Cesantías 2023", "Valor": intereses_cesantias_2023, "Estado": "No Pagada"},
    {"Concepto": f"Cesantías Proporcionales 2024 ({FECHA_INICIO_CESANTIAS_2024.strftime('%b %d')} - {FECHA_FIN_CESANTIAS_2024.strftime('%b %d')})", "Valor": cesantias_2024_proporcional, "Estado": "No Pagada"},
    {"Concepto": "Intereses sobre Cesantías Proporcionales 2024", "Valor": intereses_cesantias_2024_proporcional, "Estado": "No Pagada"},
    {"Concepto": f"Vacaciones Compensadas ({FECHA_INICIO_VACACIONES.strftime('%b %d, %Y')} - {FECHA_FIN_VACACIONES.strftime('%b %d, %Y')})", "Valor": vacaciones_compensadas, "Estado": "No Pagada"}
]
df_liquidacion = pd.DataFrame(liquidacion_items)
df_liquidacion["Valor"] = df_liquidacion["Valor"].round().astype(int)

total_liquidacion_no_pagada = df_liquidacion[df_liquidacion["Estado"] == "No Pagada"]["Valor"].sum()
df_total_liquidacion_row = pd.DataFrame([{"Concepto": "TOTAL LIQUIDACIÓN NO PAGADA", "Valor": total_liquidacion_no_pagada, "Estado": ""}])
df_liquidacion_reporte = pd.concat([df_liquidacion, df_total_liquidacion_row], ignore_index=True)

print("\n--- DETALLE DE LIQUIDACIÓN ---")
print(df_liquidacion_reporte.to_string(index=False))
print("\n")


# ============================
# 5. CÁLCULO DE INDEMNIZACIONES Y SANCIONES
# ============================

# --- 5.1 Indemnización por Mora en Pago de Liquidación (Art. 65 CST) ---
# Un día de salario por cada día de mora, contado desde la terminación del contrato.
FECHA_LIMITE_PAGO_LIQUIDACION = FECHA_FIN_CONTRATO 
dias_retraso_liquidacion = (FECHA_ACTUAL_CALCULO - FECHA_LIMITE_PAGO_LIQUIDACION).days if FECHA_ACTUAL_CALCULO > FECHA_LIMITE_PAGO_LIQUIDACION else 0

# El salario diario para esta indemnización es el último salario promedio devengado,
# o el salario base si no hay datos para promediar el último mes.
salario_diario_para_mora_liquidacion = SALARIO_DIARIO_CONTRACTUAL
indemnizacion_mora_liquidacion = salario_diario_para_mora_liquidacion * dias_retraso_liquidacion

# --- 5.2 Sanción por No Consignación Oportuna de Cesantías (Ley 50/90 Art. 99) ---
# Cesantías de 2023 debieron consignarse antes del 15 de febrero de 2024.
FECHA_LIMITE_CONSIGNACION_CESANTIAS_2023 = datetime(2024, 2, 15) # Fecha legal máxima
dias_retraso_consignacion_cesantias = (FECHA_ACTUAL_CALCULO - FECHA_LIMITE_CONSIGNACION_CESANTIAS_2023).days
dias_retraso_consignacion_cesantias = max(0, dias_retraso_consignacion_cesantias)

# Salario base para esta sanción: último salario mensual vigente al 31 de diciembre de 2023.
# Se extrae el salario base de los desprendibles de diciembre de 2023.
paystubs_dec_2023 = df_paystubs[
    (df_paystubs['Period_Start_Date'].dt.year == 2023) &
    (df_paystubs['Period_Start_Date'].dt.month == 12)
]
# Sumar el 'base_salary' de los periodos de pago que caen en diciembre.
# Si los periodos son quincenales, esto sumaría las dos quincenas.
salario_mensual_vigente_dic2023 = paystubs_dec_2023['base_salary'].sum()

if salario_mensual_vigente_dic2023 == 0 and not paystubs_dec_2023.empty:
    # Si hay registros de diciembre pero la suma es 0, podría ser un error de datos.
    # O si el salario base fue 0 ese mes.
    # Se puede tomar el promedio del periodo de cesantías 2023.
    salario_mensual_vigente_dic2023 = base_cesantias_2023_calc['avg_monthly_base_salary_only_for_formula']
    print(f"Advertencia: Salario base de Dic 2023 es 0 en paystubs. Usando promedio de cesantías 2023: {salario_mensual_vigente_dic2023:.0f}")


if salario_mensual_vigente_dic2023 == 0: # Si sigue siendo 0 (no hay datos de Dic o el promedio fue 0)
    salario_mensual_vigente_dic2023 = SALARIO_BASE_CONTRACTUAL # Fallback al salario contractual
    print(f"Advertencia: No se pudo determinar el salario de Dic 2023. Usando salario contractual: {SALARIO_BASE_CONTRACTUAL:.0f}")

salario_diario_sancion_cesantias = salario_mensual_vigente_dic2023 / 30
sancion_mora_consignacion_cesantias = salario_diario_sancion_cesantias * dias_retraso_consignacion_cesantias

# --- 5.3 Indemnización por Despido Indirecto (o sin justa causa) ---
# Esta fórmula es más común para contratos a término indefinido (1er año: 30 días, >1 año: 20 días + adicionales).
dias_totales_servicio = calcular_dias_laborados(FECHA_INICIO_CONTRATO, FECHA_FIN_CONTRATO)
# Usar SALARIO_BASE_CONTRACTUAL como base para esta indemnización, no promedios.
# indemnizacion_despido_indirecto = round((SALARIO_BASE_CONTRACTUAL / 30) * (dias_totales_servicio / 365.0) * 30) # Ejemplo: 30 días por año
indemnizacion_despido_indirecto = round(SALARIO_BASE_CONTRACTUAL / 360 * dias_totales_servicio)

# --- 5.4 Reporte de Indemnizaciones y Sanciones ---
indemnizaciones_items = [
    {"Concepto": "Indemnización por mora en pago de liquidación (Art. 65 CST)",
     "Valor": round(indemnizacion_mora_liquidacion)},
    {"Concepto": f"  (Días mora: {dias_retraso_liquidacion}, Salario día base: {round(salario_diario_para_mora_liquidacion)})",
     "Valor": ""}, # Detalle, sin valor numérico sumable
    {"Concepto": "Sanción por no consignación Cesantías 2023 (Ley 50/90 Art. 99)",
     "Valor": round(sancion_mora_consignacion_cesantias)},
    {"Concepto": f"  (Días mora: {dias_retraso_consignacion_cesantias}, Salario día base sanción: {round(salario_diario_sancion_cesantias)})",
     "Valor": ""}, # Detalle
    {"Concepto": "Indemnización por Despido Indirecto (según cálculo original)",
     "Valor": round(indemnizacion_despido_indirecto)}
]

df_indemnizaciones = pd.DataFrame(indemnizaciones_items)
# Convertir la columna 'Valor' a numérico, los strings vacíos se volverán NaN
df_indemnizaciones['Valor'] = pd.to_numeric(df_indemnizaciones['Valor'], errors='coerce')

total_indemnizaciones_sanciones = df_indemnizaciones["Valor"].sum() # Suma solo los valores numéricos

df_total_indemnizaciones_row = pd.DataFrame([{
    "Concepto": "TOTAL INDEMNIZACIONES Y SANCIONES",
    "Valor": round(total_indemnizaciones_sanciones)
}])
df_indemnizaciones_reporte = pd.concat([df_indemnizaciones.fillna({'Valor': ''}), df_total_indemnizaciones_row], ignore_index=True)


print("\n--- INDEMNIZACIONES Y SANCIONES ---")
print(f"Cálculos realizados a fecha: {FECHA_ACTUAL_CALCULO.strftime('%Y-%m-%d')}")
print(df_indemnizaciones_reporte.to_string(index=False))


# ============================
# 6. MONTO TOTAL DE LAS PRETENSIONES
# ============================
monto_total_pretensiones = total_liquidacion_no_pagada + total_indemnizaciones_sanciones

print("\n--- MONTO TOTAL DE LAS PRETENSIONES ---")
print(f"Monto total de las pretensiones: {round(monto_total_pretensiones):,}")
print("==========================================")