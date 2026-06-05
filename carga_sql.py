
# carga_sql.py  —  Paso 3 del ETL: Carga de datos a MySQL con SQLAlchemy

# Este script lee el CSV procesado que dejó transformacion.py y lo inserta
# en la base de datos MySQL. Usamos SQLAlchemy porque nos permite construir
# el "engine" de conexión de forma dinámica desde config.py, sin poner
# contraseñas en el código.
#
#  solo necesita modificar config.py con sus credenciales.
#      Este archivo NO debe tocarse.

import pandas as pd                      # para leer el CSV procesado
from sqlalchemy import create_engine, text  # SQLAlchemy para conectar a MySQL
from pathlib import Path                 # rutas portables sin C:\Users\...
import sys                               # para salir limpio si algo falla

# Importamos la configuración centralizada — aquí están las credenciales
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, TABLA_PRINCIPAL

# --- Ruta del CSV procesado ---
BASE_DIR          = Path(__file__).parent
ARCHIVO_PROCESADO = BASE_DIR / "datos" / "procesado" / "datos_inflacion_procesado.csv"


def crear_base_de_datos(engine):
    """
    Crea la base de datos si no existe.
    Esto lo hacemos con una conexión sin especificar la BD todavía,
    para no fallar si la BD aún no existe.
    """
    # Usamos text() porque SQLAlchemy moderno requiere que las queries en crudo
    # vayan envueltas así — lo aprendimos en clase
    cadena_sin_bd = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}"
    engine_temp   = create_engine(cadena_sin_bd)
    with engine_temp.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4"))
        conn.execute(text(f"USE `{DB_NAME}`"))
        conn.commit()
    print(f"✅ Base de datos '{DB_NAME}' lista")


def crear_tabla(engine):
    """
    Crea la tabla principal si no existe.
    La estructura de columnas aquí debe coincidir EXACTAMENTE con
    lo que genera transformacion.py — si no, el INSERT falla.
    """
    sql_create = f"""
    CREATE TABLE IF NOT EXISTS `{TABLA_PRINCIPAL}` (
        id                         INT AUTO_INCREMENT PRIMARY KEY,
        fecha_registro             DATE           NOT NULL,
        inpc_general               DECIMAL(10, 4) NULL,
        tipo_cambio_dolar          DECIMAL(10, 4) NULL,
        salario_minimo_diario      DECIMAL(10, 4) NULL,
        inflacion_mensual_porc     DECIMAL(8,  4) NULL,
        inflacion_anual_porc       DECIMAL(8,  4) NULL,
        salario_real_base2012      DECIMAL(10, 4) NULL,
        poder_adquisitivo_relativo DECIMAL(8,  4) NULL,
        sexenio                    VARCHAR(60)    NULL,
        UNIQUE KEY uq_fecha (fecha_registro)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    with engine.connect() as conn:
        conn.execute(text(sql_create))
        conn.commit()
    print(f"✅ Tabla '{TABLA_PRINCIPAL}' lista")


def cargar_csv():
    """
    Lee el CSV procesado. Si no existe, probablemente no se corrió transformacion.py.
    Usamos un error descriptivo para que sea fácil entender qué hacer.
    """
    if not ARCHIVO_PROCESADO.exists():
        print(f"❌ No se encontró: {ARCHIVO_PROCESADO}")
        print("   Corre primero transformacion.py y vuelve a intentar.")
        sys.exit(1)

    df = pd.read_csv(ARCHIVO_PROCESADO, parse_dates=["fecha_registro"])
    print(f"  CSV cargado: {len(df)} registros con {len(df.columns)} columnas")
    return df


def insertar_datos(df, engine):
    """
    Inserta los datos en MySQL. Usamos el método 'replace' de pandas
    que internamente hace INSERT OR REPLACE, así que si ya hay datos
    de una corrida anterior los actualiza en lugar de duplicarlos.
    Sin embargo, como la tabla tiene UNIQUE KEY en fecha_registro,
    usamos to_sql con if_exists='append' y manejamos duplicados con
    ON DUPLICATE KEY UPDATE directamente con la llave única.
    """
    # Separamos fecha para asegurarnos de que va como DATE y no como TIMESTAMP
    df["fecha_registro"] = df["fecha_registro"].dt.date

    # Primero borramos los registros existentes para hacer una carga limpia
    # En producción haríamos un upsert, pero para un proyecto universitario
    # con pocos datos esto está bien y es más simple de entender
    with engine.connect() as conn:
        conn.execute(text(f"DELETE FROM `{TABLA_PRINCIPAL}`"))
        conn.commit()
    print("  Tabla limpiada — insertando datos frescos...")

    # to_sql de pandas es la forma más limpia de insertar un DataFrame completo
    # method='multi' hace que pandas agrupe los inserts para ser más eficiente
    df.to_sql(
        name       = TABLA_PRINCIPAL,
        con        = engine,
        if_exists  = "append",   # la tabla ya existe (la creamos arriba), solo añadimos
        index      = False,       # no queremos que pandas meta el índice como columna extra
        method     = "multi",     # inserts en lote, más rápido que uno por uno
        chunksize  = 500          # en bloques de 500 para no saturar MySQL
    )

    # Verificamos cuántos registros quedaron en la BD para confirmar que sí entró todo
    with engine.connect() as conn:
        resultado = conn.execute(text(f"SELECT COUNT(*) FROM `{TABLA_PRINCIPAL}`"))
        total_bd  = resultado.fetchone()[0]

    print(f"✅ Inserción completa: {total_bd} registros en '{TABLA_PRINCIPAL}'")


def cargar():
    """Función principal que orquesta todos los pasos de carga."""
    print("=" * 60)
    print("  PASO 3 — Carga de datos a MySQL")
    print("=" * 60 + "\n")

    # Creamos el engine sin la BD todavía para poder crearla si no existe
    crear_base_de_datos(create_engine(
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}"
    ))

    # Ahora sí creamos el engine apuntando a la BD correcta
    cadena_con_bd = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine        = create_engine(cadena_con_bd, echo=False)

    # Verificamos conexión
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Engine listo")
    except Exception as e:
        print(f"❌ Fallo al conectar con la BD '{DB_NAME}': {e}")
        sys.exit(1)

    crear_tabla(engine)

    df = cargar_csv()
    insertar_datos(df, engine)

    print(f"\n{'='*60}")
    print("  Carga a MySQL completada")
    print(f"  Base de datos : {DB_NAME}")
    print(f"  Tabla         : {TABLA_PRINCIPAL}")
    print("=" * 60)


if __name__ == "__main__":
    cargar()