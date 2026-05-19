import requests
import pandas as pd

# Token oficial del proyecto
token = "a2b76ab8387bf1e7c3c8070df84c894558548efbab676f435813a7249433280e"


def extraer_datos_inflacion():
    # ID de la serie de INPC General
    serie = "SP1"
    url = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{serie}/datos"
    headers = {"Bmx-Token": token}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        raw_data = data['bmx']['series'][0]['datos']
        df = pd.DataFrame(raw_data)
        # Aqui guardo el raw para que Chan lo procese
        df.to_csv("datos_inflacion_raw.csv", index=False)
        print("Extracción completa. Archivo generado.")
    else:
        print("Error en la conexión con Banxico")


if __name__ == "__main__":
    extraer_datos_inflacion()