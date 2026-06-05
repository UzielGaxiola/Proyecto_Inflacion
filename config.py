
# config.py  —  Configuración de la base de datos MySQL

# INSTRUCCIONES PARA EL PROFESOR:
#   Este es el ÚNICO archivo que necesita modificar para que el proyecto
#   funcione en su computadora. Cambie los valores de abajo con sus
#   credenciales locales de MySQL y listo. Ningún otro archivo tiene
#   contraseñas o rutas hardcodeadas.


# Host donde corre MySQL — casi siempre es "localhost" si lo tiene instalado local
DB_HOST = "localhost"

# Puerto de MySQL — el default es 3306, cámbielo solo si lo configuró diferente
DB_PORT = 3306

# Usuario de MySQL — normalmente es "root" en instalaciones locales
DB_USER = "root"

# Contraseña de su MySQL — esta es la que usted definió al instalar MySQL
DB_PASSWORD = "su_password"

# Nombre de la base de datos — el script carga_sql.py la crea si no existe
DB_NAME = "inflacion_mexico"

# Nombre de la tabla principal — usado en carga_sql.py y en el Dashboard
# Si lo cambia aquí, se actualiza automáticamente en todos lados
TABLA_PRINCIPAL = "datos_inflacion"