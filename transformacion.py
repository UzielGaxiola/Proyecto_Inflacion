# transformacion.py  —  Paso 2 del ETL: Limpieza y transformación de los datos
# Aquí tomamos el CSV crudo que dejó extraccion.py y lo convertimos en algo
# usable. Limpiamos fechas, calculamos inflación mensual y anual, asignamos
# el sexenio a cada registro, y al final guardamos un CSV procesado listo
# para que carga_sql.py lo meta a MySQL.
#
# También incluimos los salarios mínimos oficiales de CONASAMI como respaldo,
# por si la serie SL11298 de Banxico no devolvió datos.

import pandas as pd          # para todo el manejo de datos
import numpy as np           # para operaciones numéricas (aunque pd ya trae bastante)
from pathlib import Path     # rutas portables, nada de C:\Users\...

# --- Rutas ---
BASE_DIR  = Path(__file__).parent
RAW_DIR   = BASE_DIR / "datos" / "raw"
PROC_DIR  = BASE_DIR / "datos" / "procesado"

ARCHIVO_RAW       = RAW_DIR  / "datos_banxico_raw.csv"
ARCHIVO_PROCESADO = PROC_DIR / "datos_inflacion_procesado.csv"

# --- Salarios mínimos oficiales CONASAMI ---
# Fuente: https://www.gob.mx/conasami
# Los usamos como respaldo si la API de Banxico no entregó la serie SL11298.
# Esto fue idea del equipo para no depender solo de la API.
SALARIOS_CONASAMI = {
    2012: 62.33,  2013: 64.76,  2014: 67.29,
    2015: 70.10,  2016: 73.04,  2017: 80.04,  2018: 88.36,
    2019: 102.68, 2020: 123.22, 2021: 141.70,  2022: 172.87,
    2023: 207.44, 2024: 248.93, 2025: 278.00
}

# --- Definición de sexenios ---
# Peña Nieto arrancó en dic 2012, AMLO en dic 2018, Sheinbaum en oct 2024
SEXENIOS = [
    ("Peña Nieto",  pd.Timestamp("2012-12-01"), pd.Timestamp("2018-11-30")),
    ("AMLO",        pd.Timestamp("2018-12-01"), pd.Timestamp("2024-09-30")),
    ("Sheinbaum",   pd.Timestamp("2024-10-01"), pd.Timestamp("2030-12-31")),
]


def asignar_sexenio(fecha):
    """
    Recibe una fecha y regresa el nombre del presidente en turno.
    Si cae fuera de todos los rangos, regresa 'Otro' para no perder la fila.
    """
    for nombre, inicio, fin in SEXENIOS:
        if inicio <= fecha <= fin:
            return nombre
    return "Otro"


def cargar_raw():
    """Carga el CSV crudo que generó extraccion.py."""
    if not ARCHIVO_RAW.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo raw en: {ARCHIVO_RAW}\n"
            "Asegúrate de haber corrido extraccion.py primero."
        )
    df = pd.read_csv(ARCHIVO_RAW)
    print(f"  Registros cargados del raw  : {len(df)}")
    print(f"  Series disponibles          : {df['serie'].unique().tolist()}")
    return df


def limpiar_y_pivotar(df):
    """
    Convierte las columnas de texto a tipos correctos y pivota la tabla
    para que cada serie quede como una columna separada (una fila = un mes).
    """
    # La fecha viene como string "01/12/2012" o "2012-12-01" dependiendo de la serie
    df["fecha"] = pd.to_datetime(df["fecha"], dayfirst=True, errors="coerce")
    df["dato"]  = pd.to_numeric(df["dato"], errors="coerce")

    # Quitamos filas donde la fecha o el valor no se pudieron convertir
    antes = len(df)
    df    = df.dropna(subset=["fecha", "dato"])
    print(f"  Filas eliminadas por NaN    : {antes - len(df)}")

    # Estandarizamos todo a primer día del mes (algunas series son diarias)
    # Esto nos permite hacer el join entre series de distinta frecuencia
    df["periodo"] = df["fecha"].dt.to_period("M").dt.to_timestamp()

    # Si hay varias lecturas del mismo mes (ej. tipo de cambio diario), promediamos
    df_pivot = (
        df.groupby(["periodo", "serie"])["dato"]
        .mean()
        .unstack("serie")
        .reset_index()
        .rename(columns={"periodo": "fecha_registro"})
    )

    print(f"  Periodos después del pivot  : {len(df_pivot)}")
    print(f"  Columnas disponibles        : {df_pivot.columns.tolist()}")
    return df_pivot


def agregar_salario(df):
    """
    Agrega la columna de salario mínimo diario.
    Primero intenta usar los datos que bajó Banxico (SP30268 = 'salario_minimo').
    Si no hay suficientes datos de la API, usa el respaldo de CONASAMI.
    """
    # Renombrar la columna de la API si existe
    if "salario_minimo" in df.columns and df["salario_minimo"].notna().sum() > 5:
        df["salario_minimo_diario"] = df["salario_minimo"]
        # El salario solo cambia una o dos veces al año, así que rellenamos los meses
        # intermedios con el último valor conocido (eso hace ffill)
        df["salario_minimo_diario"] = df["salario_minimo_diario"].ffill().bfill()
        print("  Salario mínimo: datos de Banxico (SP30268)")
    else:
        # Respaldo con datos de CONASAMI — asignamos el salario según el año de cada fila
        df["salario_minimo_diario"] = df["fecha_registro"].apply(
            lambda f: SALARIOS_CONASAMI.get(f.year, None)
        )
        print("  Salario mínimo: datos CONASAMI (respaldo)")

    # Limpiamos la columna intermedia si quedó
    df = df.drop(columns=["salario_minimo"], errors="ignore")
    return df


def calcular_metricas(df):
    """
    Calcula todas las columnas derivadas que necesitamos para el análisis.
    Aquí está el corazón del ETL: transformamos datos crudos en indicadores.
    """
    # -- Inflación mensual --
    # pct_change() calcula el cambio porcentual respecto al mes anterior
    # Multiplicamos por 100 para que quede como porcentaje (ej. 0.5 → "0.5%")
    if "inpc_general" in df.columns:
        df["inflacion_mensual_porc"] = df["inpc_general"].pct_change() * 100

        # -- Inflación anual --
        # Comparamos con el mismo mes del año pasado (12 periodos atrás)
        # Esto es la fórmula oficial que usa INEGI para reportar la inflación anual
        df["inflacion_anual_porc"] = df["inpc_general"].pct_change(periods=12) * 100

        # -- Salario real base 2012 --
        # El salario real nos dice cuánto "alcanza" ese salario descontando la inflación.
        # Lo calculamos dividiendo el salario nominal entre el INPC y multiplicando
        # por el INPC del año base (2012), para que los valores sean comparables en el tiempo.
        # Fórmula: Salario_Real = (Salario_Nominal / INPC_actual) * INPC_base
        inpc_base = df["inpc_general"].dropna().iloc[0]  # primer valor = base 2012
        df["salario_real_base2012"] = (
            (df["salario_minimo_diario"] / df["inpc_general"]) * inpc_base
        ).round(4)

        # -- Poder adquisitivo relativo --
        # Qué fracción del poder de compra original conserva $1 peso en cada mes.
        # Si vale 0.50, quiere decir que $1 peso solo compra lo que compraban $0.50 en 2012.
        df["poder_adquisitivo_relativo"] = (inpc_base / df["inpc_general"]).round(4)

    # -- Sexenio --
    # Le ponemos la etiqueta del presidente a cada fila para poder filtrar en el Dashboard
    df["sexenio"] = df["fecha_registro"].apply(asignar_sexenio)

    # -- Renombrar tipo de cambio si la columna viene con nombre distinto de la API --
    if "tipo_cambio_dolar" not in df.columns:
        for posible in ["SF43718", "tc_dolar"]:
            if posible in df.columns:
                df = df.rename(columns={posible: "tipo_cambio_dolar"})
                break

    return df


def seleccionar_columnas_finales(df):
    """
    Nos quedamos solo con las columnas que va a necesitar la base de datos.
    Esto evita meter columnas basura o intermedias a MySQL.
    """
    columnas_deseadas = [
        "fecha_registro",
        "inpc_general",
        "tipo_cambio_dolar",
        "salario_minimo_diario",
        "inflacion_mensual_porc",
        "inflacion_anual_porc",
        "salario_real_base2012",
        "poder_adquisitivo_relativo",
        "sexenio"
    ]
    # Solo tomamos las que realmente existen (por si alguna serie no se descargó)
    columnas_disponibles = [c for c in columnas_deseadas if c in df.columns]
    df = df[columnas_disponibles].copy()

    # Redondeamos las columnas numéricas para no llenar la BD de decimales innecesarios
    cols_num = df.select_dtypes(include="number").columns
    df[cols_num] = df[cols_num].round(4)

    # Quitamos filas donde el INPC sea nulo (sin INPC no podemos calcular nada)
    df = df.dropna(subset=["inpc_general"])

    print(f"  Columnas finales            : {df.columns.tolist()}")
    print(f"  Registros listos para carga : {len(df)}")
    return df


def transformar():
    """Función principal que orquesta todos los pasos de transformación."""
    print("=" * 60)
    print("  PASO 2 — Transformación y limpieza de datos")
    print("=" * 60 + "\n")

    # Creamos la carpeta de salida si no existe
    PROC_DIR.mkdir(parents=True, exist_ok=True)

    df = cargar_raw()
    df = limpiar_y_pivotar(df)
    df = agregar_salario(df)
    df = calcular_metricas(df)
    df = seleccionar_columnas_finales(df)

    # Guardamos el CSV procesado — carga_sql.py lo leerá desde aquí
    df.to_csv(ARCHIVO_PROCESADO, index=False)

    print(f"\n{'='*60}")
    print(f"  Transformación completa")
    print(f"  Archivo procesado: {ARCHIVO_PROCESADO}")
    print("=" * 60)


if __name__ == "__main__":
    transformar()