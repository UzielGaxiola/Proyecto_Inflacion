
# 📊 Proyecto: Análisis de Inflación y Poder Adquisitivo en México

Este proyecto es un sistema integral de datos (ETL + Dashboard interactivo) diseñado para analizar el impacto económico de la inflación, el tipo de cambio y el salario mínimo en el poder adquisitivo en México a lo largo de los últimos tres sexenios.

---

## 🛠️ Requisitos y Justificación de Librerías

Antes de correr el proyecto, se deben instalar las dependencias ejecutando este comando en la terminal:

```bash
pip install pandas numpy requests urllib3 sqlalchemy pymysql streamlit plotly statsmodels
Justificación técnica de las librerías:

requests y urllib3: Para conectar con la API de Banxico de forma segura y manejar reintentos si falla el servidor.

pandas y numpy: Para limpiar datos nulos, estandarizar fechas y calcular la inflación mensual/anual y el salario real.

sqlalchemy y pymysql: Para conectar Python con MySQL, permitiendo estructurar y cargar los datos de forma automatizada y segura.

streamlit: Para levantar la interfaz web interactiva de forma rápida usando solo Python.

plotly y statsmodels: Para generar las gráficas financieras interactivas y trazar líneas de tendencia económica.

👨‍🏫 Instrucciones paso a paso para ejecutar el proyecto
Paso 1: Crear la Base de Datos en MySQL
Abra el archivo de base de datos y corralo antes de iniciar el etl


Paso 2: Configurar Credenciales
Abra el archivo config.py en la raíz del proyecto. Modifique únicamente las siguientes variables con sus datos locales de MySQL:

DB_HOST = "localhost"

DB_PORT = 3306

DB_USER = "su_usuario"

DB_PASSWORD = "su_contraseña"

Paso 3: Ejecutar el pipeline ETL (Extracción, Transformación y Carga)
Ejecute los siguientes scripts
Extracción: Descarga los datos históricos en crudo desde la API de Banxico.


python extraccion.py
Transformación: Limpia los datos, aplica el respaldo de CONASAMI y calcula las métricas.


python transformacion.py
Carga: Conecta a MySQL y puebla la tabla datos_inflacion dentro de la base de datos.


python carga_sql.py
Paso 4: Lanzar el Dashboard
Una vez cargados los datos, ejecute el siguiente comando para abrir la aplicación interactiva:

Bash
streamlit run Interfaz.py
El sistema abrirá automáticamente el panel visual en su navegador web.

👥 Equipo de Desarrollo
Gaxiola Elizalde Uziel Hiram

Merin Zepeda Esteban Gabriel

Chan Lauro Joseph

Materia: Programación para la extracción de datos

Universidad Autónoma de Baja California (UABC)
