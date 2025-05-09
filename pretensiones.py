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
smlmv_2024 = 1_300_000

# Define los periodos para el cálculo de cada prestación
fecha_inicio_prima1_2023 = datetime(2023, 4, 17)
fecha_fin_prima1_2023 = datetime(2023, 6, 30)
fecha_inicio_prima2_2023 = datetime(2023, 7, 1)
fecha_fin_prima2_2023 = datetime(2023, 12, 31)
fecha_inicio_prima_2024 = datetime(2024, 1, 1)
fecha_fin_prima_2024 = datetime(2024, 2, 17)

fecha_inicio_cesantias_2023 = datetime(2023, 4, 17)
fecha_fin_cesantias_2023 = datetime(2023, 12, 31)
fecha_inicio_cesantias_2024 = datetime(2024, 1, 1)
fecha_fin_cesantias_2024 = datetime(2024, 1, 1) # Corrección: El periodo va hasta la fecha de fin de contrato
fecha_fin_cesantias_2024 = fecha_fin_contrato

fecha_inicio_vacaciones = fecha_inicio_contrato
fecha_fin_vacaciones = fecha_fin_contrato


# ============================
# 2. CARGA Y PREPROCESAMIENTO DE DATOS
# ============================
# Carga el archivo CSV con la información de los desprendibles de nómina
df_paystubs = pd.read_csv('paystubs-summary.csv')

# Convierte las columnas de fechas al formato datetime de Python
# 'pay_period_starts' y 'pay_period_ends' deberían contener las fechas de inicio y fin de cada periodo de pago
df_paystubs['Period_Start_Date'] = pd.to_datetime(
    df_paystubs['pay_period_starts'], dayfirst=False)
df_paystubs['Period_End_Date'] = pd.to_datetime(
    df_paystubs['pay_period_ends'], dayfirst=False)

# Extrae el año y el mes para facilitar el análisis mensual
df_paystubs['Year'] = df_paystubs['Period_Start_Date'].dt.year
df_paystubs['Month_Int'] = df_paystubs['Period_Start_Date'].dt.month
df_paystubs['year_month_period'] = df_paystubs['Period_Start_Date'].dt.to_period(
    'M')

# Mapeo de números de mes a nombres en español (opcional, para mejor comprensión)
month_map_es = {
    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
    5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
}
df_paystubs['Month_Name_ES'] = df_paystubs['Month_Int'].map(month_map_es)

# Define las columnas correspondientes a los "extras" salariales
extras_cols = ['sunday_bonus', 'holiday_bonus',
               'night_bonus', 'day_overtime', 'night_overtime']

# Asegura que las columnas numéricas sean tratadas como números y rellena los valores vacíos con 0
for col in extras_cols + ['base_salary', 'aux_transp']:
    df_paystubs[col] = pd.to_numeric(
        df_paystubs[col], errors='coerce').fillna(0).astype(int)

# Calcula el total de los extras para cada periodo de pago
df_paystubs['total_extras'] = df_paystubs[extras_cols].sum(axis=1)

# --- 2. Resumen Financiero Mensual (Abril 2023 - Febrero 2024) ---
monthly_summary_list = []

# Agrupa los datos por periodo mensual para calcular los totales mensuales
for month_period_obj, group in df_paystubs.groupby('year_month_period'):
    monthly_base_salary = group['base_salary'].sum()
    monthly_extras = group['total_extras'].sum()
    # Salario mensual = Salario base + Extras
    monthly_salary = monthly_base_salary + monthly_extras
    monthly_aux_transporte = group['aux_transp'].sum()

    # Ingreso Base de Cotización (IBC) para pensión: Salario mensual + Auxilio de Transporte
    monthly_ibc = monthly_salary + monthly_aux_transporte
    # Aporte a Pensión (12% es la suma del aporte del empleador y el empleado)
    monthly_aporte_pension = monthly_ibc * 0.12

    monthly_summary_list.append({
        "Month": month_period_obj.strftime('%Y-%m'),
        "Base Salary": monthly_base_salary,
        "Extras": monthly_extras,
        "Total Salary (Base + Extras)": monthly_salary,
        "Auxilio Transporte": monthly_aux_transporte,
        "IBC (Ingreso Base Cotización)": monthly_ibc,
        # Redondea el valor final
        "Aporte Pensión (12%)": round(monthly_aporte_pension)
    })

df_monthly_report = pd.DataFrame(monthly_summary_list)

# Filtra el reporte para el periodo de interés: Abril 2023 a Febrero 2024
start_report_month = pd.Period('2023-04', freq='M')
end_report_month = pd.Period('2024-02', freq='M')
df_monthly_report['Month_Period_Obj'] = pd.PeriodIndex(
    df_monthly_report['Month'], freq='M')
df_monthly_report = df_monthly_report[
    (df_monthly_report['Month_Period_Obj'] >= start_report_month) &
    (df_monthly_report['Month_Period_Obj'] <= end_report_month)
].drop(columns=['Month_Period_Obj'])

print("--- RESUMEN FINANCIERO MENSUAL (Abril 2023 - Febrero 2024) ---")
print(df_monthly_report.to_string(index=False))
print("\n")


# ============================
# 3. Calculo prestaciones de liquidación
# ============================


def calcular_dias_laborados(inicio, fin):
    """Calcula el número de días trabajados entre dos fechas (inclusive)"""
    if inicio > fin:
        return 0
    return (fin - inicio).days + 1


def get_proportional_earnings_for_period(df_ps, period_start, period_end):
    """
    Calcula el salario base, extras y auxilio de transporte proporcionales para un periodo dado.
    Estos valores se utilizan para calcular el promedio mensual para las fórmulas de liquidación.
    """
    total_pro_rata_base_salary = 0.0
    total_pro_rata_extras = 0.0
    total_pro_rata_aux_transp = 0.0

    num_days_in_calc_period = calcular_dias_laborados(period_start, period_end)

    for _, row in df_ps.iterrows():
        ps_start = row['Period_Start_Date']
        ps_end = row['Period_End_Date']

        # Calcula la intersección entre el periodo de pago y el periodo de cálculo
        overlap_start = max(period_start, ps_start)
        overlap_end = min(period_end, ps_end)

        if overlap_start <= overlap_end:
            overlap_days = calcular_dias_laborados(overlap_start, overlap_end)
            days_in_pay_period = calcular_dias_laborados(ps_start, ps_end)

            if days_in_pay_period == 0:
                continue

            # Calcula la proporción del periodo de pago que se traslapa con el periodo de cálculo
            ratio = overlap_days / days_in_pay_period

            # Calcula los valores proporcionales para el periodo de cálculo
            total_pro_rata_base_salary += row['base_salary'] * ratio
            total_pro_rata_extras += row['total_extras'] * ratio
            total_pro_rata_aux_transp += row['aux_transp'] * ratio

    if num_days_in_calc_period == 0:
        avg_monthly_salary_for_formula = 0.0
        avg_monthly_aux_for_formula = 0.0
        avg_monthly_base_salary_only_for_formula = 0.0
    else:
        # Salario base para la liquidación = Salario base + Extras (promedio mensual)
        avg_monthly_salary_for_formula = (
            total_pro_rata_base_salary + total_pro_rata_extras) / num_days_in_calc_period * 30
        # Auxilio de transporte promedio mensual
        avg_monthly_aux_for_formula = total_pro_rata_aux_transp / num_days_in_calc_period * 30
        # Salario base promedio mensual (solo base, para vacaciones)
        avg_monthly_base_salary_only_for_formula = total_pro_rata_base_salary / \
            num_days_in_calc_period * 30

    return {
        "avg_monthly_salary_for_formula": avg_monthly_salary_for_formula,
        "avg_monthly_aux_for_formula": avg_monthly_aux_for_formula,
        "avg_monthly_base_salary_only_for_formula": avg_monthly_base_salary_only_for_formula,
        "worked_days_in_period": num_days_in_calc_period,
    }

# Cálculo de la Prima de Servicios
base_prima1 = get_proportional_earnings_for_period(
    df_paystubs, fecha_inicio_prima1_2023, fecha_fin_prima1_2023)
prima_1_2023 = (base_prima1['avg_monthly_salary_for_formula'] +
                base_prima1['avg_monthly_aux_for_formula']) * base_prima1['worked_days_in_period'] / 360
# Ecuación: (Salario promedio mensual + Auxilio de transporte promedio mensual) * Días trabajados en el semestre / 360

base_prima2 = get_proportional_earnings_for_period(
    df_paystubs, fecha_inicio_prima2_2023, fecha_fin_prima2_2023)
prima_2_2023 = (base_prima2['avg_monthly_salary_for_formula'] +
                base_prima2['avg_monthly_aux_for_formula']) * base_prima2['worked_days_in_period'] / 360
# Ecuación: (Salario promedio mensual + Auxilio de transporte promedio mensual) * Días trabajados en el semestre / 360

base_prima3 = get_proportional_earnings_for_period(
    df_paystubs, fecha_inicio_prima_2024, fecha_fin_prima_2024)
prima_2024 = (base_prima3['avg_monthly_salary_for_formula'] +
              base_prima3['avg_monthly_aux_for_formula']) * base_prima3['worked_days_in_period'] / 360
# Ecuación: (Salario promedio mensual + Auxilio de transporte promedio mensual) * Días trabajados en el periodo / 360

# Cálculo de las Cesantías
base_cesantias_2023 = get_proportional_earnings_for_period(
    df_paystubs, fecha_inicio_cesantias_2023, fecha_fin_cesantias_2023)
cesantias_2023 = (base_cesantias_2023['avg_monthly_salary_for_formula'] +
                  base_cesantias_2023['avg_monthly_aux_for_formula']) * base_cesantias_2023['worked_days_in_period'] / 360
# Ecuación: (Salario promedio mensual + Auxilio de transporte promedio mensual) * Días trabajados en el año / 360

base_cesantias_2024 = get_proportional_earnings_for_period(
    df_paystubs, fecha_inicio_cesantias_2024, fecha_fin_cesantias_2024)
cesantias_2024 = (base_cesantias_2024['avg_monthly_salary_for_formula'] +
                  base_cesantias_2024['avg_monthly_aux_for_formula']) * base_cesantias_2024['worked_days_in_period'] / 360
# Ecuación: (Salario promedio mensual + Auxilio de transporte promedio mensual) * Días trabajados en el periodo / 360

# Cálculo de los Intereses sobre las Cesantías (12% anual)
intereses_cesantias_2023 = (
    cesantias_2023 * base_cesantias_2023['worked_days_in_period'] * 0.12) / 360
# Ecuación: (Cesantías * Días trabajados en el año * 0.12) / 360

intereses_cesantias_2024 = (
    cesantias_2024 * base_cesantias_2024['worked_days_in_period'] * 0.12) / 360
# Ecuación: (Cesantías proporcionales * Días trabajados en el periodo * 0.12) / 360

# Cálculo de las Vacaciones
base_vacaciones = get_proportional_earnings_for_period(
    df_paystubs, fecha_inicio_vacaciones, fecha_fin_vacaciones)
vacaciones = (base_vacaciones['avg_monthly_base_salary_only_for_formula']
              * base_vacaciones['worked_days_in_period']) / 720
# Ecuación: (Salario base promedio mensual * Días trabajados en el periodo) / 720 (ya que se pagan 15 días por año trabajado)

# Reporte de Liquidación
liquidacion_items = [
    {"Concepto": "Prima 1er Semestre 2023 (Abr 17 - Jun 30)",
     "Valor": prima_1_2023, "Estado": "Pagada"},
    {"Concepto": "Prima 2do Semestre 2023 (Jul 01 - Dic 31)",
     "Valor": prima_2_2023, "Estado": "Pagada"},
    {"Concepto": "Prima Proporcional 2024 (Ene 01 - Feb 17)",
     "Valor": prima_2024, "Estado": "No Pagada"},
    {"Concepto": "Cesantías 2023 (Abr 17 - Dic 31)",
     "Valor": cesantias_2023, "Estado": "No Pagada"},
    {"Concepto": "Intereses sobre Cesantías 2023",
        "Valor": intereses_cesantias_2023, "Estado": "No Pagada"},
    {"Concepto": "Cesantías Proporcionales 2024 (Ene 01 - Feb 17)",
     "Valor": cesantias_2024, "Estado": "No Pagada"},
    {"Concepto": "Intereses sobre Cesantías Proporcionales 2024",
        "Valor": intereses_cesantias_2024, "Estado": "No Pagada"},
    {"Concepto": "Vacaciones (Abr 17, 2023 - Feb 17, 2024)",
     "Valor": vacaciones, "Estado": "No Pagada"}
]
df_liquidacion = pd.DataFrame(liquidacion_items)
df_liquidacion["Valor"] = df_liquidacion["Valor"].round().astype(
    int)  # Redondea los valores a enteros

total_liquidacion_no_pagada = df_liquidacion[df_liquidacion["Estado"] != "Pagada"]["Valor"].sum(
)
total_row = pd.DataFrame([{"Concepto": "Valor total de liquidación (No Pagado)",
                         "Valor": total_liquidacion_no_pagada, "Estado": ""}])
df_liquidacion = pd.concat([df_liquidacion, total_row], ignore_index=True)

print("\n--- DETALLE DE LIQUIDACIÓN ---")
print(df_liquidacion.to_string(index=False))
print("\n")

# ============================
# 4. INDEMNIZACIÓN POR MORA EN LIQUIDACIÓN
# ============================
# salario_base = 2_100_000
salario_diario = salario_base / 30
fecha_limite_pago_liquidacion = fecha_fin_contrato + timedelta(days=15)
dias_retraso_liquidacion = (fecha_actual - fecha_limite_pago_liquidacion).days if fecha_actual > fecha_limite_pago_liquidacion else 0

# La indemnización es un día de salario por cada día de mora.
indemnizacion_mora_liquidacion = salario_diario * dias_retraso_liquidacion

# ============================
# 4. SANCIÓN POR CESANTÍAS NO CONSIGNADAS
# ============================
# Sanción por no consignación oportuna de las Cesantías 2023 (Artículo 99 de la Ley 50 de 1990)
# Las cesantías del año 2023 debieron ser consignadas antes del 15 de febrero de 2024.
fecha_limite_consignacion_cesantias_2023 = datetime(2024, 2, 15)
dias_retraso_consignacion_cesantias = (fecha_actual - fecha_limite_consignacion_cesantias_2023).days if fecha_actual > fecha_limite_consignacion_cesantias_2023 else 0

# El salario diario para esta sanción es el último salario vigente al 31 de diciembre de 2023.
# Se extrae el salario base de los desprendibles correspondientes a diciembre de 2023.
diciembre_start = datetime(2023, 12, 1)
enero_start = datetime(2024, 1, 1)

salario_mensual_vigente_dic2023 = df_paystubs[
    (df_paystubs['Period_Start_Date'] >= diciembre_start) &
    (df_paystubs['Period_Start_Date'] < enero_start)
]['base_salary'].sum()  # Suma de los salarios base de los periodos en diciembre

# En caso de no encontrar datos de diciembre, usa el salario de referencia
if salario_mensual_vigente_dic2023 == 0:
    salario_mensual_vigente_dic2023 = salario_base

# La sanción es un día de salario por cada día de mora en la consignación.
sancion_mora_consignacion_cesantias = salario_diario * dias_retraso_consignacion_cesantias

# ============================
# 5. INDEMNIZACIÓN POR DESPIDO INDIRECTO
# ============================

dias_servicio = (fecha_fin_contrato - fecha_inicio_contrato).days
indemnizacion_despido = round(salario_base / 360 * dias_servicio)

# ============================
# 6. REPORTE DE INDEMNIZACIONES Y SANCIONES
# ============================
 
indemnizaciones_items = [
    {"Concepto": "Indemnización por mora en pago de liquidación (Art. 65 CST)", "Valor": round(indemnizacion_mora_liquidacion)},
    {"Concepto": f"(Días mora: {dias_retraso_liquidacion}, Salario día: {round(salario_diario)})", "Valor": ""},
    {"Concepto": "Sanción por no consignación Cesantías 2023 (Ley 50/90 Art. 99)", "Valor": round(sancion_mora_consignacion_cesantias)},
    {"Concepto": f"(Días mora: {dias_retraso_consignacion_cesantias}, Salario día: {round(salario_diario)})", "Valor": ""},
    {"Concepto": "Indemnización por Despido Indirecto", "Valor": indemnizacion_despido}
]

# Cálculo total
total_indemnizaciones = indemnizacion_mora_liquidacion + sancion_mora_consignacion_cesantias + indemnizacion_despido

# Genera DataFrame
df_indemnizaciones = pd.DataFrame(indemnizaciones_items)
total_indem_row = pd.DataFrame([{ "Concepto": "Total Indemnizaciones y Sanciones", "Valor": round(total_indemnizaciones) }])
df_indemnizaciones = pd.concat([df_indemnizaciones, total_indem_row], ignore_index=True)

print("\n--- INDEMNIZACIONES Y SANCIONES POR MORA ---")
print(f"Cálculos realizados a fecha: {fecha_actual.strftime('%Y-%m-%d %H:%M:%S')}")
print(df_indemnizaciones.to_string(index=False))

# ============================
# 7. MONTO TOTAL DE LAS PRETENSIONES
# ============================

# Asegúrate de que esta variable esté definida antes en tu script:
# total_liquidacion_no_pagada = df_liquidacion[df_liquidacion["Estado"] != "Pagada"]["Valor"].sum()

monto_total_pretensiones = total_liquidacion_no_pagada + total_indemnizaciones

print("\n--- MONTO TOTAL DE LAS PRETENSIONES ---")
print(f"Monto total de las pretensiones: {round(monto_total_pretensiones)}")