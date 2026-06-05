
# extraccion.py  —  Paso 1 del ETL: Extracción de datos desde la API de Banxico

# Aquí descargamos los datos directamente de la API oficial del Banco de México
# . Guardamos todo en crudo (raw) sin
# limpiar nada, eso se hace en transformacion.py. La idea es que si algo falla
# en la limpieza, siempre tengamos el dato original sin tocar.
#
# Series que usamos:
#   SP1     = INPC General mensual (el índice que mide la inflación)
#   SL11298 = Salario mínimo general diario (cambia una o dos veces al año)
#   SF43718 = Tipo de cambio FIX peso/dólar (dato diario de Banxico)


import requests                          # para hacer las peticiones a la API
from requests.adapters import HTTPAdapter  # para configurar reintentos
from urllib3.util.retry import Retry     # estrategia de reintentos en caso de fallo
import pandas as pd                      # para armar el dataframe con los registros
import time                              # para pausar entre llamadas y no saturar la API
from pathlib import Path                 # para manejar rutas de forma portable (sin C:\Users\...)

# --- Token de acceso a la API de Banxico ---
# Si este token expira, genera uno nuevo y reemplázalo aquí
TOKEN = "a2b76ab8387bf1e7c3c8070df84c894558548efbab676f435813a7249433280e"

# --- Rutas portables con pathlib ---
# Path(__file__).parent da la carpeta donde está este script, sin importar en qué PC se corra
BASE_DIR = Path(__file__).parent
RAW_DIR  = BASE_DIR / "datos" / "raw"

# --- Series que vamos a descargar ---
# Son un diccionario: clave = ID de la serie en Banxico, valor = nombre descriptivo nuestro
SERIES = {
    "SP1":     "inpc_general",       # índice de precios al consumidor
    "SL11298": "salario_minimo",     # salario mínimo oficial (CONASAMI vía Banxico)
    "SF43718": "tipo_cambio_dolar"   # peso mexicano por un dólar americano
}

# --- Rango de fechas ---
# Cubrimos los últimos 3 sexenios: Peña Nieto arrancó en dic 2012, así que desde ahí
FECHA_INICIO = "2012-12-01"
FECHA_FIN    = "2025-06-01"

# --- Headers de la petición ---
# Banxico rechaza peticiones que no traigan User-Agent (cierra la conexión sin responder).
# Eso fue el "RemoteDisconnected" que nos salió antes — solución: simular un navegador
HEADERS = {
    "Bmx-Token":      TOKEN,
    "User-Agent":     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept":         "application/json",
    "Accept-Language": "es-MX,es;q=0.9"
}


def crear_sesion():
    """
    Crea una sesión de requests con reintentos automáticos.
    Lo usamos porque a veces la API de Banxico tiene picos de carga
    y falla en el primer intento — con esto reintenta sola hasta 3 veces.
    """
    sesion    = requests.Session()
    reintentos = Retry(
        total=3,              # máximo 3 intentos por llamada
        backoff_factor=2,     # espera 2, 4, 8 segundos entre intentos
        status_forcelist=[429, 500, 502, 503, 504]  # códigos de error que sí reintentar
    )
    sesion.mount("https://", HTTPAdapter(max_retries=reintentos))
    return sesion


def validar_token(sesion):
    """
    Hace una llamada rápida para verificar si el token sirve antes de descargar todo.
    Mejor saber desde aquí que el token expiró a que explote a la mitad.
    """
    url = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/SP1/datos/oportuno"
    try:
        r = sesion.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 401:
            print("❌ Token inválido o expirado.")
            print("   Genera uno nuevo en: https://www.banxico.org.mx/SieAPIRest/service/v1/token")
            return False
        if r.status_code == 200:
            print("✅ Token válido.\n")
            return True
        # Si llega un código inesperado, lo imprimimos para saber qué pasó
        print(f"⚠️  Código inesperado al validar token: {r.status_code}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Error de conexión: {e}")
        print("   Verifica que tengas internet y vuelve a intentar.")
        return False


def extraer_serie(sesion, serie_id, nombre):
    """
    Descarga una serie específica de Banxico en el rango de fechas definido arriba.
    Regresa un DataFrame con las columnas: fecha, dato, serie, serie_id.
    Si algo falla, regresa None para que el programa pueda continuar con las otras series.
    """
    # Construimos la URL con el formato que pide la API (YYYY-MM-DD obligatorio)
    url = (
        f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/"
        f"{serie_id}/datos/{FECHA_INICIO}/{FECHA_FIN}"
    )

    print(f"  Descargando: {nombre} ({serie_id})...")

    try:
        respuesta = sesion.get(url, headers=HEADERS, timeout=20)
    except requests.exceptions.ConnectionError as e:
        print(f"  ❌ Fallo de conexión en {serie_id}: {e}")
        return None
    except requests.exceptions.Timeout:
        print(f"  ⏱️  Timeout en {serie_id} — se omite esta serie")
        return None

    # Si la API regresó error HTTP, lo reportamos y seguimos con la siguiente serie
    if respuesta.status_code != 200:
        print(f"  ⚠️  Error {respuesta.status_code} en {serie_id}: {respuesta.text[:120]}")
        return None

    # Intentamos parsear el JSON — a veces la respuesta viene sin el campo 'datos'
    # (por ejemplo cuando el ID de la serie no existe), así que lo protegemos con try-except
    try:
        data       = respuesta.json()
        info_serie = data["bmx"]["series"][0]
        if "datos" not in info_serie:
            print(f"  ⚠️  La serie {serie_id} no devolvió datos (quizás el ID cambió en Banxico)")
            return None
        registros = info_serie["datos"]
    except (KeyError, IndexError, ValueError) as e:
        print(f"  ❌ Error al leer respuesta de {serie_id}: {e}")
        return None

    # Banxico marca los valores faltantes como "N/E" — los filtramos para no meter basura
    registros = [r for r in registros if r.get("dato", "N/E") not in ("N/E", "N/A", "")]

    if not registros:
        print(f"  ⚠️  Sin registros válidos para {serie_id} en el rango {FECHA_INICIO} – {FECHA_FIN}")
        return None

    # Armamos el DataFrame y le ponemos etiquetas para saber de qué serie viene cada fila
    df             = pd.DataFrame(registros)
    df["serie"]    = nombre
    df["serie_id"] = serie_id

    print(f"  ✅ {len(df)} registros descargados")
    return df


def extraer_todas_las_series():
    """
    Función principal: valida el token, descarga todas las series y guarda el CSV crudo.
    """
    print("=" * 60)
    print("  PASO 1 — Extracción de datos desde Banxico")
    print("=" * 60 + "\n")

    # Creamos la carpeta de destino si no existe (pathlib hace esto fácil)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    sesion = crear_sesion()

    # Primero verificamos el token para no perder tiempo si ya expiró
    if not validar_token(sesion):
        return

    frames   = []
    exitosas = 0

    for serie_id, nombre in SERIES.items():
        df = extraer_serie(sesion, serie_id, nombre)
        if df is not None:
            frames.append(df)
            exitosas += 1
        # Pausa de 1.5 segundos entre llamadas para no banear nuestra IP
        time.sleep(1.5)

    sesion.close()

    # Si no bajó ninguna serie, no tiene caso guardar nada
    if not frames:
        print("\n❌ No se pudo obtener ninguna serie. Revisa el token y tu conexión.")
        return

    # Concatenamos todos los DataFrames en uno solo y lo guardamos como CSV crudo
    df_raw = pd.concat(frames, ignore_index=True)
    ruta_salida = RAW_DIR / "datos_banxico_raw.csv"
    df_raw.to_csv(ruta_salida, index=False)

    print(f"\n{'='*60}")
    print(f"  Extracción terminada")
    print(f"  Series exitosas : {exitosas} / {len(SERIES)}")
    print(f"  Total registros : {len(df_raw)}")
    print(f"  Archivo RAW     : {ruta_salida}")
    print("=" * 60)


# Punto de entrada del script
if __name__ == "__main__":
    extraer_todas_las_series()