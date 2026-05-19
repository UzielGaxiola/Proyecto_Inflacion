import pandas as pd


def procesar_informacion():
    # aqui cargo el archivo de Uziel
    df = pd.read_csv("datos_inflacion_raw.csv")

    # limpiamos las fechas del archivo
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce', format='mixed')

    # Limpiamos los valores y los convertimos a numericos
    df['dato'] = pd.to_numeric(df['dato'], errors='coerce')
    df = df.dropna(subset=['dato'])

    # cambiamos el nombre para la Base de Datos
    df.columns = ['fecha_registro', 'valor_inpc']

    # Guardamos el archivo limpio para Merin
    df.to_csv("datos_inflacion_limpios.csv", index=False)
    print("Limpieza de datos terminada con éxito")

if __name__ == '__main__':
    procesar_informacion()