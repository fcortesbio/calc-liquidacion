import pandas as pd
from datetime import datetime, timedelta
import calendar

# Load the dataframe
df_paystubs = pd.read_csv('paystubs-summary.csv')
######### Debugging: Verify how many reports are read
print("Cantidad de registros en paystubs:", len(df_paystubs))

# Load and process dataframe columns
# Parse dates based on the label column to handle formats like "16 al 30 de Abril 2023"

# First, parse the periods from 'label' column
def parse_period_string(period_str):
    """
    Parses strings like "16 al 30 de Abril 2023" or "16 al 17 de febrero de 2024"
    Returns the start_date, end_date, month_name, year of the period.
    This function will parse the END date of the period for assigning month/year.
    """
    parts = period_str.split(' de ')
    
    try:
        year = int(parts[-1])
        month_name_es = parts[-2].strip().lower()
    except (ValueError, IndexError):
        # Special case for "febrero de 2024"
        if len(parts) > 1 and "febrero de 2024" in period_str:
            month_name_es = "febrero"
            year = 2024
        else:
            # Special case for simple "Month YYYY" format
            try:
                words = period_str.split()
                month_name_es = words[0].lower()
                year = int(words[1])
            except (IndexError, ValueError):
                # If all else fails, assume current month/year
                current_date = datetime.now()
                month_name_es = {
                    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril', 
                    5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
                    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
                }[current_date.month]
                year = current_date.year
    
    month_map_es_to_int = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
        'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
    }
    month_int = month_map_es_to_int[month_name_es]
    
    try:
        # Only try to extract days if the format looks like "DD al DD ..."
        if "al" in parts[0]:
            day_parts = parts[0].replace("al ", "").split()
            start_day = int(day_parts[0])
            end_day = int(day_parts[-1])
        else:
            # Simple month format, use first and last day of month
            start_day = 1
            end_day = calendar.monthrange(year, month_int)[1]
    except (ValueError, IndexError):
        # Default to full month
        start_day = 1
        end_day = calendar.monthrange(year, month_int)[1]

    return (datetime(year, month_int, start_day), 
            datetime(year, month_int, end_day), 
            month_name_es, year, month_int)

# Process period labels and add date-based columns 
parsed_periods = [parse_period_string(p) for p in df_paystubs['label']]

# The parse_period_string function already returns datetime objects, no conversion needed
df_paystubs['Period_Start_Date'] = [p[0] for p in parsed_periods]  # Already datetime objects
df_paystubs['Period_End_Date'] = [p[1] for p in parsed_periods]    # Already datetime objects
df_paystubs['Month_Name_ES'] = [p[2] for p in parsed_periods]
df_paystubs['Year'] = [p[3] for p in parsed_periods]
df_paystubs['Month_Int'] = [p[4] for p in parsed_periods]

# Define Extras columns and ensure numeric types, fill NaNs for calculations
extras_cols = ['sunday_bonus', 'holiday_bonus', 'night_bonus', 'day_overtime', 'night_overtime']
for col in extras_cols + ['base_salary', 'aux_transp']:
    df_paystubs[col] = pd.to_numeric(df_paystubs[col], errors='coerce').fillna(0).astype(int)

df_paystubs['total_extras'] = df_paystubs[extras_cols].sum(axis=1)

# --- Part 1: Monthly Financial Summary ---
# Create a new column with period based on the datetime objects
df_paystubs['year_month_period'] = pd.Series(df_paystubs['Period_Start_Date']).dt.to_period('M')

######### Debugging:Print values of year_month_period
print("Periodos detectados en los registros:")
print(df_paystubs[['label', 'Period_Start_Date', 'year_month_period']])

monthly_summary_list = []

# Aggregate paystub data into calendar months
# This simple groupby assumes pay periods roughly align with bi-monthly splits within a calendar month
for month_period_obj, group in df_paystubs.groupby('year_month_period'):
    monthly_base_salary = group['base_salary'].sum()
    monthly_extras = group['total_extras'].sum()
    monthly_salary = monthly_base_salary + monthly_extras # Salary = Base + Extras
    monthly_aux_transporte = group['aux_transp'].sum()
    
    # IBC for pension: As per user, Salary + Aux_transporte
    monthly_ibc = monthly_salary + monthly_aux_transporte
    # Aporte Pensión (16% represents total employer + employee contribution)
    monthly_aporte_pension = monthly_ibc * 0.16 

    monthly_summary_list.append({
        "Month": month_period_obj.strftime('%Y-%m'),
        "Base Salary": monthly_base_salary,
        "Extras": monthly_extras,
        "Total Salary (Base + Extras)": monthly_salary,
        "Auxilio Transporte": monthly_aux_transporte,
        "IBC (Ingreso Base Cotización)": monthly_ibc,
        "Aporte Pensión (16%)": round(monthly_aporte_pension) # Round final pension amount
    })

df_monthly_report = pd.DataFrame(monthly_summary_list)


####### Debugging: Verify datatypes for df_monthly_report
print(df_monthly_report[['Month']])
print(df_monthly_report['Month'].dtype)


# Filter for the required range: April 2023 to February 2024
start_report_month = pd.Period('2023-04', freq='M')
end_report_month = pd.Period('2024-02', freq='M')
df_monthly_report['Month_Period_Obj'] = pd.PeriodIndex(df_monthly_report['Month'], freq='M')
df_monthly_report = df_monthly_report[
    (df_monthly_report['Month_Period_Obj'] >= start_report_month) &
    (df_monthly_report['Month_Period_Obj'] <= end_report_month)
].drop(columns=['Month_Period_Obj'])

print("--- MONTHLY FINANCIAL SUMMARY (April 2023 - February 2024) ---")
print(df_monthly_report.to_string(index=False))
print("\n")


# --- Part 2: Calculation of Severance Benefits (Liquidación) ---

# Define Key Dates
fecha_inicio_contrato = datetime(2023, 4, 17)
fecha_fin_contrato = datetime(2024, 2, 17) # Termination date

# Prima periods
fecha_inicio_prima1_2023 = datetime(2023, 4, 17); fecha_fin_prima1_2023 = datetime(2023, 6, 30)
fecha_inicio_prima2_2023 = datetime(2023, 7, 1); fecha_fin_prima2_2023 = datetime(2023, 12, 31)
fecha_inicio_prima_2024 = datetime(2024, 1, 1); fecha_fin_prima_2024 = datetime(2024, 2, 17)

# Cesantías periods
fecha_inicio_cesantias_2023 = datetime(2023, 4, 17); fecha_fin_cesantias_2023 = datetime(2023, 12, 31)
fecha_inicio_cesantias_2024 = datetime(2024, 1, 1); fecha_fin_cesantias_2024 = datetime(2024, 2, 17)

# Vacations period
fecha_inicio_vacaciones = fecha_inicio_contrato; fecha_fin_vacaciones = fecha_fin_contrato

def calcular_dias_laborados(inicio, fin):
    """Calculate days worked between two dates (inclusive)"""
    if inicio > fin:
        return 0
    return (fin - inicio).days + 1

def get_proportional_earnings_for_period(df_ps, period_start, period_end):
    """
    Calculates total pro-rata base salary, extras, and aux_transporte for a given period.
    These totals are then used to calculate average monthly values for liquidation formulas.
    """
    total_pro_rata_base_salary = 0.0
    total_pro_rata_extras = 0.0
    total_pro_rata_aux_transp = 0.0

    # Ensure period dates are datetime objects - likely not needed 
    # since we're already using datetime objects, but keeping for safety
    if not isinstance(period_start, datetime):
        period_start = pd.to_datetime(period_start)
    if not isinstance(period_end, datetime):
        period_end = pd.to_datetime(period_end)

    for _, row in df_ps.iterrows():
        # Use our parsed period dates
        ps_start = row['Period_Start_Date']
        ps_end = row['Period_End_Date']

        overlap_start = max(period_start, ps_start)
        overlap_end = min(period_end, ps_end)

        if overlap_start <= overlap_end:
            overlap_days = calcular_dias_laborados(overlap_start, overlap_end)
            days_in_pay_period = calcular_dias_laborados(ps_start, ps_end)
            
            if days_in_pay_period == 0: continue 

            ratio = overlap_days / days_in_pay_period
            
            total_pro_rata_base_salary += row['base_salary'] * ratio
            total_pro_rata_extras += row['total_extras'] * ratio
            total_pro_rata_aux_transp += row['aux_transp'] * ratio
            
    num_days_in_calc_period = calcular_dias_laborados(period_start, period_end)

    if num_days_in_calc_period == 0:
        avg_monthly_salary_for_formula = 0.0
        avg_monthly_aux_for_formula = 0.0
        avg_monthly_base_salary_only_for_formula = 0.0
    else:
        # Salary for liquidation base = base_salary + extras
        avg_monthly_salary_for_formula = (total_pro_rata_base_salary + total_pro_rata_extras) / num_days_in_calc_period * 30
        avg_monthly_aux_for_formula = total_pro_rata_aux_transp / num_days_in_calc_period * 30
        avg_monthly_base_salary_only_for_formula = total_pro_rata_base_salary / num_days_in_calc_period * 30
        
    return {
        "avg_monthly_salary_for_formula": avg_monthly_salary_for_formula,
        "avg_monthly_aux_for_formula": avg_monthly_aux_for_formula,
        "avg_monthly_base_salary_only_for_formula": avg_monthly_base_salary_only_for_formula,
        "worked_days_in_period": num_days_in_calc_period, 
    }

# Calculate Prima
base_prima1 = get_proportional_earnings_for_period(df_paystubs, fecha_inicio_prima1_2023, fecha_fin_prima1_2023)
prima_1_2023 = (base_prima1['avg_monthly_salary_for_formula'] + base_prima1['avg_monthly_aux_for_formula']) * base_prima1['worked_days_in_period'] / 360

base_prima2 = get_proportional_earnings_for_period(df_paystubs, fecha_inicio_prima2_2023, fecha_fin_prima2_2023)
prima_2_2023 = (base_prima2['avg_monthly_salary_for_formula'] + base_prima2['avg_monthly_aux_for_formula']) * base_prima2['worked_days_in_period'] / 360

base_prima3 = get_proportional_earnings_for_period(df_paystubs, fecha_inicio_prima_2024, fecha_fin_prima_2024)
prima_2024 = (base_prima3['avg_monthly_salary_for_formula'] + base_prima3['avg_monthly_aux_for_formula']) * base_prima3['worked_days_in_period'] / 360

# Calculate Cesantías
base_cesantias_2023 = get_proportional_earnings_for_period(df_paystubs, fecha_inicio_cesantias_2023, fecha_fin_cesantias_2023)
cesantias_2023 = (base_cesantias_2023['avg_monthly_salary_for_formula'] + base_cesantias_2023['avg_monthly_aux_for_formula']) * base_cesantias_2023['worked_days_in_period'] / 360

base_cesantias_2024 = get_proportional_earnings_for_period(df_paystubs, fecha_inicio_cesantias_2024, fecha_fin_cesantias_2024)
cesantias_2024 = (base_cesantias_2024['avg_monthly_salary_for_formula'] + base_cesantias_2024['avg_monthly_aux_for_formula']) * base_cesantias_2024['worked_days_in_period'] / 360

# Calculate Intereses de Cesantías (12% annual rate)
intereses_cesantias_2023 = (cesantias_2023 * base_cesantias_2023['worked_days_in_period'] * 0.12) / 360
intereses_cesantias_2024 = (cesantias_2024 * base_cesantias_2024['worked_days_in_period'] * 0.12) / 360

# Calculate Vacations
base_vacaciones = get_proportional_earnings_for_period(df_paystubs, fecha_inicio_vacaciones, fecha_fin_vacaciones)
vacaciones = (base_vacaciones['avg_monthly_base_salary_only_for_formula'] * base_vacaciones['worked_days_in_period']) / 720

# Liquidación Report
liquidacion_items = [
    {"Concepto": "Prima 1er Semestre 2023 (Apr 17 - Jun 30)", "Valor": prima_1_2023, "Estado": "Pagada"},
    {"Concepto": "Prima 2do Semestre 2023 (Jul 01 - Dec 31)", "Valor": prima_2_2023, "Estado": "Pagada"},
    {"Concepto": "Prima Proporcional 2024 (Ene 01 - Feb 17)", "Valor": prima_2024, "Estado": "No Pagada"},
    {"Concepto": "Cesantías 2023 (Apr 17 - Dec 31)", "Valor": cesantias_2023, "Estado": "No Pagada (Consignar/Liquidar)"},
    {"Concepto": "Intereses sobre Cesantías 2023", "Valor": intereses_cesantias_2023, "Estado": "No Pagada"},
    {"Concepto": "Cesantías Proporcionales 2024 (Ene 01 - Feb 17)", "Valor": cesantias_2024, "Estado": "No Pagada"},
    {"Concepto": "Intereses sobre Cesantías Proporcionales 2024", "Valor": intereses_cesantias_2024, "Estado": "No Pagada"},
    {"Concepto": "Vacaciones (Apr 17, 2023 - Feb 17, 2024)", "Valor": vacaciones, "Estado": "No Pagada"}
]
df_liquidacion = pd.DataFrame(liquidacion_items)
df_liquidacion["Valor"] = df_liquidacion["Valor"].round().astype(int) # Round final COP amounts

total_liquidacion_no_pagada = df_liquidacion[df_liquidacion["Estado"] != "Pagada"]["Valor"].sum()
# Add total row using pd.concat to avoid direct modification issues
total_row = pd.DataFrame([{"Concepto": "Valor total de liquidación (No Pagado)", "Valor": total_liquidacion_no_pagada, "Estado": ""}])
df_liquidacion = pd.concat([df_liquidacion, total_row], ignore_index=True)


print("\n--- DETALLE DE LIQUIDACIÓN ---")
print(df_liquidacion.to_string(index=False))
print("\n")

# --- Part 3: Calculation of Indemnities (Moratorias) ---
fecha_actual = datetime.now() # For real-time calculation. For testing, you can set: datetime(YYYY, M, D)

# Salario diario para indemnizaciones, based on last nominal monthly salary.
# User specified 2,100,000/30. Data for full months (e.g., Jan 2024) shows base 2,100,000.
# Feb part-time data (140,000 for 2 days) also projects to 2,100,000/month.
ultimo_salario_mensual_ref = 2_100_000 
salario_diario_indemnizacion_general = ultimo_salario_mensual_ref / 30

# 1. Indemnización por mora en liquidación (Art. 65 CST)
# User: "today - termination_date (feb 17, 2024 + 15 days)"
# This means mora starts after a 15-day grace period post-termination.
fecha_limite_pago_liquidacion = fecha_fin_contrato + timedelta(days=15)
dias_retraso_liquidacion = 0
if fecha_actual > fecha_limite_pago_liquidacion:
    dias_retraso_liquidacion = (fecha_actual - fecha_limite_pago_liquidacion).days
indemnizacion_mora_liquidacion = salario_diario_indemnizacion_general * dias_retraso_liquidacion

# 2. Sanción por no consignación oportuna de Cesantías 2023 (Ley 50 de 1990, Art. 99, Par. 3)
# Cesantías 2023 should have been consigned by Feb 14, 2024.
fecha_limite_consignacion_cesantias_2023 = datetime(2024, 2, 14)
dias_retraso_consignacion_cesantias = 0
if fecha_actual > fecha_limite_consignacion_cesantias_2023:
    dias_retraso_consignacion_cesantias = (fecha_actual - fecha_limite_consignacion_cesantias_2023).days

# Salario diario para esta sanción es el último salario vigente al 31 de diciembre de 2023.
# Base salary for Dec 2023 was 2,100,000 (1,050,000 * 2 from paystubs).

# Convert to datetime for comparison if not already
december_start = datetime(2023, 12, 1)
january_start = datetime(2024, 1, 1)

salario_mensual_vigente_dic2023 = df_paystubs[
    (df_paystubs['Period_Start_Date'] >= december_start) & 
    (df_paystubs['Period_Start_Date'] < january_start)
]['base_salary'].sum() # Should be 2,100,000

if salario_mensual_vigente_dic2023 == 0: # Fallback if data is sparse for Dec
    salario_mensual_vigente_dic2023 = ultimo_salario_mensual_ref 

salario_diario_sancion_cesantias = salario_mensual_vigente_dic2023 / 30
sancion_mora_consignacion_cesantias = salario_diario_sancion_cesantias * dias_retraso_consignacion_cesantias

# Reporte de Indemnizaciones
indemnizaciones_items = [
    {"Concepto": "Indemnización por mora en pago de liquidación (Art. 65 CST)", "Valor": round(indemnizacion_mora_liquidacion)},
    {"Concepto": f"(Días mora: {dias_retraso_liquidacion}, Salario día: {round(salario_diario_indemnizacion_general)})", "Valor": ""},
    {"Concepto": "Sanción por no consignación Cesantías 2023 (Ley 50/90 Art. 99)", "Valor": round(sancion_mora_consignacion_cesantias)},
    {"Concepto": f"(Días mora: {dias_retraso_consignacion_cesantias}, Salario día: {round(salario_diario_sancion_cesantias)})", "Valor": ""},
]
df_indemnizaciones = pd.DataFrame(indemnizaciones_items)
total_indemnizaciones = indemnizacion_mora_liquidacion + sancion_mora_consignacion_cesantias

total_indem_row = pd.DataFrame([{"Concepto": "Total Indemnizaciones y Sanciones", "Valor": round(total_indemnizaciones)}])
df_indemnizaciones = pd.concat([df_indemnizaciones, total_indem_row], ignore_index=True)

print("\n--- INDEMNIZACIONES Y SANCIONES POR MORA ---")
print(f"Cálculos realizados a fecha: {fecha_actual.strftime('%Y-%m-%d %H:%M:%S')}")
print(df_indemnizaciones.to_string(index=False))

# Monto total de las pretensiones
monto_total_pretensiones = total_liquidacion_no_pagada + total_indemnizaciones
print("\n--- MONTO TOTAL DE LAS PRETENSIONES ---")
print(f"Monto total de las pretensiones: {round(monto_total_pretensiones)}")