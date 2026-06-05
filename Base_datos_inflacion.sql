
-- base_datos_inflacion.sql
-- Proyecto: Inflación y Poder Adquisitivo en México
-- Materia:  Bases de Datos / ETL y Visualización de Datos

-- INSTRUCCIONES:
--   1. Abrir este archivo en MySQL Workbench o desde la terminal con:
--         mysql -u root -p < base_datos_inflacion.sql
--   2. Esto crea la base de datos y la tabla con la estructura exacta
--      que necesita carga_sql.py para insertar los datos del ETL.
--   3. Los 5 INSERTs al final son de prueba para verificar la estructura.
--      carga_sql.py borrará estos registros y cargará los datos reales.


-- Creamos la base de datos si no existe (no truena si ya existe)
CREATE DATABASE IF NOT EXISTS inflacion_mexico
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Nos movemos a esa base de datos
USE inflacion_mexico;

-- Tabla principal: datos_inflacion
-- Columnas exactas que genera transformacion.py
-- IMPORTANTE: el nombre "datos_inflacion" debe coincidir con TABLA_PRINCIPAL
--             en config.py — si lo cambia aquí, cámbielo también allá.

CREATE TABLE IF NOT EXISTS datos_inflacion (
    -- Clave primaria autoincremental — MySQL la genera sola
    id                         INT            AUTO_INCREMENT PRIMARY KEY,

    -- Fecha del registro (primer día del mes, ej. 2015-01-01)
    fecha_registro             DATE           NOT NULL,

    -- INPC General: índice base del que deriva la inflación
    -- Fuente serie SP1 de Banxico
    inpc_general               DECIMAL(10, 4) NULL,

    -- Tipo de cambio FIX promedio mensual (pesos por dólar)
    -- Fuente serie SF43718 de Banxico
    tipo_cambio_dolar          DECIMAL(10, 4) NULL,

    -- Salario mínimo general diario oficial
    -- Fuente: serie SP30268 de Banxico o CONASAMI como respaldo
    salario_minimo_diario      DECIMAL(10, 4) NULL,

    -- Variación porcentual del INPC vs el mes anterior
    -- Calculado en transformacion.py con pct_change()
    inflacion_mensual_porc     DECIMAL(8,  4) NULL,

    -- Variación porcentual del INPC vs el mismo mes del año anterior
    -- Esta es la inflación "oficial" que reporta INEGI
    inflacion_anual_porc       DECIMAL(8,  4) NULL,

    -- Salario real ajustado a poder adquisitivo de diciembre 2012
    -- Muestra cuánto alcanzaba ese salario en términos de 2012
    salario_real_base2012      DECIMAL(10, 4) NULL,

    -- Fracción del poder de compra original que conserva $1 peso
    -- 1.0 = mismo poder que en 2012 | 0.5 = solo compra la mitad
    poder_adquisitivo_relativo DECIMAL(8,  4) NULL,

    -- Nombre del presidente en turno durante ese mes
    -- Valores posibles: 'Peña Nieto', 'AMLO', 'Sheinbaum'
    sexenio                    VARCHAR(60)    NULL,

    -- Evitamos duplicados por fecha (no queremos dos filas del mismo mes)
    UNIQUE KEY uq_fecha (fecha_registro)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Inserts de prueba (5 registros para verificar la estructura)
-- La rúbrica pide algunos inserts de ejemplo para agilizar la revisión.
-- carga_sql.py borrará estos y cargará los datos reales del ETL.

-- 1. Inicio del sexenio de Peña Nieto (datos aproximados)
INSERT IGNORE INTO datos_inflacion
    (fecha_registro, inpc_general, tipo_cambio_dolar, salario_minimo_diario,
     inflacion_mensual_porc, inflacion_anual_porc,
     salario_real_base2012, poder_adquisitivo_relativo, sexenio)
VALUES
    ('2013-01-01', 104.1600, 12.7600, 64.76,
     0.1800, 3.2500,
     64.76, 1.0000, 'Peña Nieto');

-- 2. Mitad del sexenio de Peña Nieto (año de baja inflación)
INSERT IGNORE INTO datos_inflacion
    (fecha_registro, inpc_general, tipo_cambio_dolar, salario_minimo_diario,
     inflacion_mensual_porc, inflacion_anual_porc,
     salario_real_base2012, poder_adquisitivo_relativo, sexenio)
VALUES
    ('2016-06-01', 118.5600, 18.4500, 73.04,
     0.3200, 2.5400,
     64.18, 0.8784, 'Peña Nieto');

-- 3. Inicio del sexenio de AMLO (con devaluación por COVID-19)
INSERT IGNORE INTO datos_inflacion
    (fecha_registro, inpc_general, tipo_cambio_dolar, salario_minimo_diario,
     inflacion_mensual_porc, inflacion_anual_porc,
     salario_real_base2012, poder_adquisitivo_relativo, sexenio)
VALUES
    ('2020-04-01', 109.4200, 24.1700, 123.22,
     0.1500, 2.1500,
     117.27, 0.9516, 'AMLO');

-- 4. Pico de inflación post-pandemia (máximo histórico reciente)
INSERT IGNORE INTO datos_inflacion
    (fecha_registro, inpc_general, tipo_cambio_dolar, salario_minimo_diario,
     inflacion_mensual_porc, inflacion_anual_porc,
     salario_real_base2012, poder_adquisitivo_relativo, sexenio)
VALUES
    ('2022-08-01', 131.2800, 19.9400, 172.87,
     0.6100, 8.7000,
     137.32, 0.7934, 'AMLO');

-- 5. Inicio del sexenio de Sheinbaum
INSERT IGNORE INTO datos_inflacion
    (fecha_registro, inpc_general, tipo_cambio_dolar, salario_minimo_diario,
     inflacion_mensual_porc, inflacion_anual_porc,
     salario_real_base2012, poder_adquisitivo_relativo, sexenio)
VALUES
    ('2024-11-01', 136.8900, 20.2400, 278.00,
     0.4200, 4.5500,
     211.90, 0.7607, 'Sheinbaum');


-- Verificación: consulta para confirmar que los inserts entraron bien
SELECT
    sexenio,
    COUNT(*)                              AS registros,
    ROUND(AVG(inflacion_anual_porc), 2)   AS inflacion_prom,
    ROUND(MIN(tipo_cambio_dolar), 2)      AS tc_minimo,
    ROUND(MAX(tipo_cambio_dolar), 2)      AS tc_maximo
FROM datos_inflacion
GROUP BY sexenio
ORDER BY MIN(fecha_registro);