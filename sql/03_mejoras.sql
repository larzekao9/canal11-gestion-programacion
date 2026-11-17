-- =====================================================================
-- Mejoras de la base de datos: las reglas de negocio que ya valida la capa N*
-- (NParrilla, NSpot, NUsuario) se refuerzan tambien en la propia BD.
-- Se puede ejecutar varias veces (DROP ... IF EXISTS antes de cada ADD CONSTRAINT).
-- Antes de aplicarlo, el Instalador revisa que los datos existentes no violen
-- estas restricciones y, si las violan, lo informa en vez de fallar.
-- =====================================================================

-- 1) Un bloque PROGRAMA lleva programa; una PAUSA_COMERCIAL no lleva programa ni material.
ALTER TABLE bloque DROP CONSTRAINT IF EXISTS ck_bloque_tipo;
ALTER TABLE bloque ADD CONSTRAINT ck_bloque_tipo CHECK (
    (tipo = 'PROGRAMA' AND id_programa IS NOT NULL)
    OR (tipo = 'PAUSA_COMERCIAL' AND id_programa IS NULL AND id_material IS NULL)
);

-- 2) Dos bloques de la misma parrilla no pueden solaparse: [hora_inicio, hora_fin).
--    Usa tsrange sobre una fecha fija para no crear un tipo timerange (no es repetible).
--    Si el servidor no permite CREATE EXTENSION (permisos), solo avisa y el instalador sigue:
--    el solape queda validado unicamente por NParrilla.
DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS btree_gist;
    ALTER TABLE bloque DROP CONSTRAINT IF EXISTS ex_bloque_sin_solape;
    ALTER TABLE bloque ADD CONSTRAINT ex_bloque_sin_solape EXCLUDE USING gist (
        id_parrilla WITH =,
        tsrange(DATE '2000-01-01' + hora_inicio, DATE '2000-01-01' + hora_fin, '[)') WITH &&
    );
EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'AVISO: no se pudo crear ex_bloque_sin_solape (%). El solape de bloques solo se valida en la aplicacion.', SQLERRM;
END
$$;

-- 3) Un spot solo va en una pausa comercial, dentro de su horario, con material SPOT aprobado.
--    Se dispara solo al cambiar id_bloque, id_material o hora: el UPDATE de estado que hace
--    DEmision.actualizarSpots NO vuelve a validar el material (pudo ser rechazado despues).
CREATE OR REPLACE FUNCTION fn_validar_spot() RETURNS trigger AS $$
DECLARE
    b bloque%ROWTYPE;
    m material%ROWTYPE;
BEGIN
    SELECT * INTO b FROM bloque WHERE id_bloque = NEW.id_bloque;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'El bloque del spot no existe.';
    END IF;
    IF b.tipo <> 'PAUSA_COMERCIAL' THEN
        RAISE EXCEPTION 'Un spot solo puede ubicarse en una pausa comercial.';
    END IF;
    IF NEW.hora < b.hora_inicio OR NEW.hora >= b.hora_fin THEN
        RAISE EXCEPTION 'La hora del spot (%) debe estar dentro de la pausa comercial (% a %).',
            NEW.hora, b.hora_inicio, b.hora_fin;
    END IF;
    SELECT * INTO m FROM material WHERE id_material = NEW.id_material;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'El material del spot no existe.';
    END IF;
    IF m.tipo <> 'SPOT' THEN
        RAISE EXCEPTION 'El material % no es de tipo SPOT.', m.codigo;
    END IF;
    IF m.estado <> 'APROBADO' THEN
        RAISE EXCEPTION 'El material % no esta APROBADO (estado: %).', m.codigo, m.estado;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_validar_spot ON spot;
CREATE TRIGGER trg_validar_spot
    BEFORE INSERT OR UPDATE OF id_bloque, id_material, hora ON spot
    FOR EACH ROW EXECUTE FUNCTION fn_validar_spot();

-- 4) El correo es unico sin importar mayusculas (Ana@x.com = ana@x.com).
CREATE UNIQUE INDEX IF NOT EXISTS ux_usuario_email_lower ON usuario (lower(email));

-- 5) Indices sobre llaves foraneas que se consultan al listar, reportar o dar de baja.
CREATE INDEX IF NOT EXISTS idx_bloque_programa    ON bloque (id_programa);
CREATE INDEX IF NOT EXISTS idx_bloque_material    ON bloque (id_material);
CREATE INDEX IF NOT EXISTS idx_material_programa  ON material (id_programa);
CREATE INDEX IF NOT EXISTS idx_material_registrado ON material (registrado_por);
CREATE INDEX IF NOT EXISTS idx_material_validado  ON material (validado_por);
CREATE INDEX IF NOT EXISTS idx_spot_pauta         ON spot (id_pauta);
CREATE INDEX IF NOT EXISTS idx_spot_material      ON spot (id_material);

-- 6) NO se aplica ON DELETE SET NULL a auditoria.id_usuario: los usuarios solo se dan de baja
--    logica y SET NULL borraria en silencio quien hizo cada cambio. La FK queda como esta.
