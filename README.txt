PROYECTO: ANÁLISIS DE INFLACIÓN Y PODER ADQUISITIVO EN MÉXICO
Este proyecto es un sistema integral de datos (ETL + Dashboard interactivo) diseñado para analizar el impacto económico de la inflación, el tipo de cambio y el salario mínimo en el poder adquisitivo de las familias mexicanas a lo largo de los últimos tres sexenios (Peña Nieto, AMLO y Sheinbaum).

TECNOLOGÍAS Y JUSTIFICACIÓN DE LIBRERÍAS
El proyecto está desarrollado en Python y se conecta a una base de datos MySQL. Para ejecutarlo, instale las siguientes dependencias ejecutando este comando en su terminal:

pip install pandas numpy requests urllib3 sqlalchemy pymysql streamlit plotly statsmodels

Justificación técnica de las librerías utilizadas:

Fase de Extracción y Transformación:

requests y urllib3: Utilizadas para gestionar la conexión a la API REST de Banxico, manejar los encabezados de autenticación (tokens) y establecer estrategias de reintento en caso de caídas del servidor.

pandas y numpy: Fundamentales para la limpieza de datos nulos, estandarización de fechas, y para ejecutar los cálculos matemáticos matriciales (como las variaciones porcentuales del INPC y el cálculo del salario real).

Fase de Carga (Base de Datos):

sqlalchemy: Actúa como un motor robusto para administrar la conexión a la base de datos. Permite crear dinámicamente el esquema en MySQL e insertar los datos limpios sin necesidad de escribir sentencias SQL vulnerables a inyecciones.

pymysql: Es el driver nativo que traduce las instrucciones de SQLAlchemy para que el servidor MySQL las pueda ejecutar correctamente.

Fase de Visualización (Dashboard):

streamlit: Framework elegido para desarrollar la interfaz web (frontend) y el sistema de navegación entre dashboards interactivos utilizando exclusivamente Python, optimizando el tiempo de desarrollo.

plotly: Utilizada para el renderizado de gráficas financieras interactivas (líneas, barras, dispersión), permitiendo a los usuarios explorar los datos exactos al pasar el cursor (hovertemplates).

statsmodels: Dependencia matemática necesaria para que Plotly pueda trazar las líneas de tendencia (regresión lineal OLS) en las gráficas de correlación entre el Dólar y la Inflación.

INSTRUCCIONES PARA EL PROFESOR (CÓMO CORRER EL PROYECTO)
Para ejecutar este proyecto localmente y visualizar el Dashboard, por favor siga estos pasos en orden:

Paso 1: Configurar las credenciales de la Base de Datos
Abra el archivo "config.py" ubicado en la raíz del proyecto. Este es el único archivo que necesita modificar. Cambie las siguientes variables para que coincidan con sus credenciales locales de MySQL:

DB_HOST (Usualmente "localhost")

DB_PORT (Usualmente 3306)

DB_USER (Su usuario de MySQL, ej. "root")

DB_PASSWORD (Su contraseña de MySQL)

(Nota: No es necesario crear la base de datos manualmente en Workbench, el código de Python la creará de manera automática).

Paso 2: Ejecutar el pipeline ETL (Extracción, Transformación y Carga)
Abra su terminal o línea de comandos, navegue hasta la carpeta del proyecto y ejecute los siguientes scripts en orden:

Extracción:
Comando: python extraccion.py
(Se conectará a la API de Banxico para descargar las series históricas en crudo).

Transformación:
Comando: python transformacion.py
(Limpiará los datos, calculará métricas y generará el archivo procesado).

Carga a MySQL:
Comando: python carga_sql.py
(Se conectará a su MySQL local, creará la BD "inflacion_mexico" y la poblará).

Paso 3: Lanzar el Dashboard Interactivo
Una vez que la base de datos esté poblada, inicie la interfaz gráfica ejecutando el siguiente comando:

Comando: streamlit run Interfaz.py

Esto abrirá automáticamente una pestaña en su navegador web (usualmente en http://localhost:8501) donde podrá interactuar con los tres dashboards analíticos del proyecto.

EQUIPO DE DESARROLLO
Gaxiola Elizalde Uziel Hiram

Merin Zepeda Esteban Gabriel

Chan Lauro Joseph

Materia: Programación para la extracción de datos
Universidad Autónoma de Baja California (UABC)