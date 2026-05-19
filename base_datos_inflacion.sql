create database if not exists inflacion_mexico;
use inflacion_mexico;

-- tabla para almacenar los registros del INPC
create table if not exists historico_inpc (
    id int auto_increment primary key,
    fecha_registro date not null,
    valor_inpc decimal(10,4) not null
);

-- inserts de pruebas
insert into historico_inpc (fecha_registro, valor_inpc) values ('2024-01-01', 133.0510);
insert into historico_inpc (fecha_registro, valor_inpc) values ('2024-02-01', 133.1700);
insert into historico_inpc (fecha_registro, valor_inpc) values ('2024-03-01', 133.5610);
insert into historico_inpc (fecha_registro, valor_inpc) values ('2025-01-01', 135.5400);