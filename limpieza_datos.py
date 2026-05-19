import pandas as pd

def procesar_informacion():
    # Cargo los datos
    df = pd.read_csv("datos_inflacion_raw.csv")

    # Limpieza básica
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce', format='mixed')
    df['dato'] = pd.to_numeric(df['dato'], errors='coerce')
    df = df.dropna(subset=['dato']).sort_values('fecha')

    # Cambio de nombre
    df.columns = ['fecha_registro', 'valor_inpc']


    #  Cálculo de Inflación Mensual (Comparado con el mes anterior)
    # Fórmula: ((Mes Actual / Mes Anterior) - 1) * 100
    df['inflacion_mensual_porc'] = df['valor_inpc'].pct_change() * 100

    #  Cálculo de Inflación Anual (Comparado con el mismo mes del año pasado)
    # Como los datos son mensuales, comparamos con 12 filas atrás
    df['inflacion_anual_porc'] = df['valor_inpc'].pct_change(periods=12) * 100

    #  Cálculo de Poder Adquisitivo (¿Cuánto vale 1 peso de hoy en el pasado?)
    # Tomamos el último valor del INPC como referencia
    ultimo_inpc = df['valor_inpc'].iloc[-1]
    df['poder_adquisitivo_relativo'] = df['valor_inpc'] / ultimo_inpc

    # Redondeo para que se vea limpio
    df = df.round(4)

    # Guardo el archivo final
    df.to_csv("datos_inflacion_limpios.csv", index=False)
    print("¡Limpieza y ANALÍTICA terminada con éxito!")

if __name__ == '__main__':
    procesar_informacion()