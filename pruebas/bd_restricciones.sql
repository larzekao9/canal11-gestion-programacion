-- =====================================================================
-- Pruebas de las restricciones de la BD (sql/03_mejoras.sql).
-- Demuestra que la propia base rechaza datos invalidos aunque la capa de negocio no los frene.
-- Todo corre dentro de una transaccion que se deshace al final: no deja datos.
--
-- Ejecutar (despues de --instalar):
--   psql -h HOST -p PUERTO -U USUARIO -d BASE -f pruebas/bd_restricciones.sql
-- Cada prueba imprime "OK  rechazado ..." (la BD la rechazo, como se espera)
-- o "FALLO  se acepto ..." (la restriccion no esta funcionando).
-- =====================================================================
\set ON_ERROR_STOP on
\pset tuples_only on
SET client_min_messages TO notice;
SET search_path TO canal11, public;

BEGIN;

-- datos de apoyo (se deshacen con el ROLLBACK final)
INSERT INTO usuario (ci, nombre, apellido, email, rol)
VALUES ('T-0001', 'Prueba', 'BD', 'Prueba.BD@Test.com', 'ADMINISTRADOR');
INSERT INTO programa (nombre, tipo, duracion_min) VALUES ('Programa Prueba BD', 'OTRO', 30);
INSERT INTO parrilla (fecha, creado_por) VALUES ('2099-01-01', (SELECT id_usuario FROM usuario WHERE ci = 'T-0001'));
INSERT INTO material (codigo, titulo, tipo, duracion_seg, formato, ruta, estado, registrado_por)
VALUES ('T-SPOT-OK', 'Spot aprobado', 'SPOT', 30, 'MP4', '/t/ok.mp4', 'APROBADO', (SELECT id_usuario FROM usuario WHERE ci = 'T-0001')),
       ('T-SPOT-PEND', 'Spot pendiente', 'SPOT', 30, 'MP4', '/t/pend.mp4', 'PENDIENTE', (SELECT id_usuario FROM usuario WHERE ci = 'T-0001'));
INSERT INTO pauta (anunciante, nombre, fecha_inicio, fecha_fin, max_pases) VALUES ('Prueba BD', 'Pauta Prueba BD', '2099-01-01', '2099-01-31', 10);
-- un bloque PROGRAMA 10:00-11:00 y una PAUSA_COMERCIAL 11:00-11:10 validos
INSERT INTO bloque (id_parrilla, id_programa, hora_inicio, hora_fin, tipo)
SELECT p.id_parrilla, (SELECT id_programa FROM programa WHERE nombre = 'Programa Prueba BD'), '10:00', '11:00', 'PROGRAMA'
FROM parrilla p WHERE p.fecha = '2099-01-01';
INSERT INTO bloque (id_parrilla, hora_inicio, hora_fin, tipo)
SELECT p.id_parrilla, '11:00', '11:10', 'PAUSA_COMERCIAL' FROM parrilla p WHERE p.fecha = '2099-01-01';

\echo '--- 1) bloque PROGRAMA sin programa (ck_bloque_tipo, esperado 23514)'
DO $$
BEGIN
    INSERT INTO bloque (id_parrilla, hora_inicio, hora_fin, tipo)
    SELECT id_parrilla, '15:00', '16:00', 'PROGRAMA' FROM parrilla WHERE fecha = '2099-01-01';
    RAISE NOTICE 'FALLO  se acepto un bloque PROGRAMA sin programa';
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'OK  rechazado [%] %', SQLSTATE, SQLERRM;
END $$;

\echo '--- 1b) PAUSA_COMERCIAL con programa (ck_bloque_tipo, esperado 23514)'
DO $$
BEGIN
    INSERT INTO bloque (id_parrilla, id_programa, hora_inicio, hora_fin, tipo)
    SELECT id_parrilla, (SELECT id_programa FROM programa WHERE nombre = 'Programa Prueba BD'), '15:00', '15:10', 'PAUSA_COMERCIAL'
    FROM parrilla WHERE fecha = '2099-01-01';
    RAISE NOTICE 'FALLO  se acepto una pausa comercial con programa';
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'OK  rechazado [%] %', SQLSTATE, SQLERRM;
END $$;

\echo '--- 2) dos bloques solapados en la misma parrilla (ex_bloque_sin_solape, esperado 23P01)'
DO $$
BEGIN
    INSERT INTO bloque (id_parrilla, hora_inicio, hora_fin, tipo)
    SELECT id_parrilla, '10:30', '11:30', 'PAUSA_COMERCIAL' FROM parrilla WHERE fecha = '2099-01-01';
    RAISE NOTICE 'FALLO  se acepto un bloque que se solapa (10:30-11:30 con 10:00-11:00)';
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'OK  rechazado [%] %', SQLSTATE, SQLERRM;
END $$;

\echo '--- 2b) bloques contiguos NO son solape (11:10-12:00 debe aceptarse)'
DO $$
BEGIN
    INSERT INTO bloque (id_parrilla, id_programa, hora_inicio, hora_fin, tipo)
    SELECT id_parrilla, (SELECT id_programa FROM programa WHERE nombre = 'Programa Prueba BD'), '11:10', '12:00', 'PROGRAMA'
    FROM parrilla WHERE fecha = '2099-01-01';
    RAISE NOTICE 'OK  aceptado (bloques pegados, como corresponde)';
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'FALLO  se rechazo un bloque contiguo [%] %', SQLSTATE, SQLERRM;
END $$;

\echo '--- 3) spot en un bloque que no es pausa comercial (fn_validar_spot, esperado P0001)'
DO $$
BEGIN
    INSERT INTO spot (id_pauta, id_material, id_bloque, hora)
    SELECT pa.id_pauta, m.id_material, b.id_bloque, '10:30'
    FROM pauta pa, material m, bloque b
    WHERE pa.nombre = 'Pauta Prueba BD' AND m.codigo = 'T-SPOT-OK' AND b.tipo = 'PROGRAMA' AND b.hora_inicio = '10:00'
      AND b.id_parrilla = (SELECT id_parrilla FROM parrilla WHERE fecha = '2099-01-01');
    RAISE NOTICE 'FALLO  se acepto un spot en un bloque PROGRAMA';
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'OK  rechazado [%] %', SQLSTATE, SQLERRM;
END $$;

\echo '--- 4) spot con material PENDIENTE (fn_validar_spot, esperado P0001)'
DO $$
BEGIN
    INSERT INTO spot (id_pauta, id_material, id_bloque, hora)
    SELECT pa.id_pauta, m.id_material, b.id_bloque, '11:02'
    FROM pauta pa, material m, bloque b
    WHERE pa.nombre = 'Pauta Prueba BD' AND m.codigo = 'T-SPOT-PEND' AND b.tipo = 'PAUSA_COMERCIAL' AND b.hora_inicio = '11:00'
      AND b.id_parrilla = (SELECT id_parrilla FROM parrilla WHERE fecha = '2099-01-01');
    RAISE NOTICE 'FALLO  se acepto un spot con material PENDIENTE';
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'OK  rechazado [%] %', SQLSTATE, SQLERRM;
END $$;

\echo '--- 4b) spot con hora fuera de la pausa (esperado P0001)'
DO $$
BEGIN
    INSERT INTO spot (id_pauta, id_material, id_bloque, hora)
    SELECT pa.id_pauta, m.id_material, b.id_bloque, '11:10'
    FROM pauta pa, material m, bloque b
    WHERE pa.nombre = 'Pauta Prueba BD' AND m.codigo = 'T-SPOT-OK' AND b.tipo = 'PAUSA_COMERCIAL' AND b.hora_inicio = '11:00'
      AND b.id_parrilla = (SELECT id_parrilla FROM parrilla WHERE fecha = '2099-01-01');
    RAISE NOTICE 'FALLO  se acepto un spot a las 11:10, fuera de la pausa 11:00-11:10';
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'OK  rechazado [%] %', SQLSTATE, SQLERRM;
END $$;

\echo '--- 4c) spot valido SI se acepta, y cambiar su estado no vuelve a validar el material'
DO $$
DECLARE
    v_id INTEGER;
BEGIN
    INSERT INTO spot (id_pauta, id_material, id_bloque, hora)
    SELECT pa.id_pauta, m.id_material, b.id_bloque, '11:02'
    FROM pauta pa, material m, bloque b
    WHERE pa.nombre = 'Pauta Prueba BD' AND m.codigo = 'T-SPOT-OK' AND b.tipo = 'PAUSA_COMERCIAL' AND b.hora_inicio = '11:00'
      AND b.id_parrilla = (SELECT id_parrilla FROM parrilla WHERE fecha = '2099-01-01')
    RETURNING id_spot INTO v_id;
    UPDATE material SET estado = 'RECHAZADO' WHERE codigo = 'T-SPOT-OK';   -- se rechaza despues de programar
    UPDATE spot SET estado = 'EMITIDO' WHERE id_spot = v_id;               -- no debe disparar la validacion
    RAISE NOTICE 'OK  spot valido aceptado y su estado se actualizo aunque el material se rechazo despues';
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'FALLO  [%] %', SQLSTATE, SQLERRM;
END $$;

\echo '--- 5) email repetido con otra capitalizacion (ux_usuario_email_lower, esperado 23505)'
DO $$
BEGIN
    INSERT INTO usuario (ci, nombre, apellido, email, rol) VALUES ('T-0002', 'Otro', 'Usuario', 'PRUEBA.bd@test.COM', 'ENCARGADO');
    RAISE NOTICE 'FALLO  se acepto un email repetido con otras mayusculas';
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'OK  rechazado [%] %', SQLSTATE, SQLERRM;
END $$;

\echo '--- 6) rol PRODUCCION permitido y un rol inventado rechazado (usuario_rol_check)'
DO $$
BEGIN
    INSERT INTO usuario (ci, nombre, apellido, email, rol) VALUES ('T-0003', 'Prod', 'Uccion', 'produccion.bd@test.com', 'PRODUCCION');
    RAISE NOTICE 'OK  rol PRODUCCION aceptado';
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'FALLO  se rechazo PRODUCCION [%] %', SQLSTATE, SQLERRM;
END $$;
DO $$
BEGIN
    INSERT INTO usuario (ci, nombre, apellido, email, rol) VALUES ('T-0004', 'Jefe', 'Falso', 'jefe.bd@test.com', 'JEFE');
    RAISE NOTICE 'FALLO  se acepto el rol JEFE';
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'OK  rechazado [%] %', SQLSTATE, SQLERRM;
END $$;

ROLLBACK;
