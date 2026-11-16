package canal11.negocio;

import canal11.datos.DBloque;
import canal11.datos.DMaterial;
import canal11.datos.DParrilla;
import canal11.datos.DPrograma;

import java.sql.SQLException;
import java.time.LocalDate;
import java.time.LocalTime;
import java.util.ArrayList;
import java.util.List;

/**
 * CU3 - Confeccionar y Controlar la Parrilla. Reglas de negocio:
 *  - Hay una parrilla por fecha. Se crea en BORRADOR; creado_por = quien envia el comando.
 *  - Una parrilla se referencia por su fecha (AAAA-MM-DD). Un bloque, por fecha + hora de inicio.
 *  - insBlo / eliBlo / eliPar solo funcionan con la parrilla en BORRADOR. Tampoco se permite quitar
 *    bloques o parrillas que ya tienen spots programados (primero se quitan con eliSpo).
 *  - Bloque: hora_fin > hora_inicio y sin solapar con otros bloques del mismo dia.
 *    PROGRAMA lleva un programa activo (obligatorio); PAUSA_COMERCIAL no lleva programa ni material.
 *    El material, si se indica, debe existir y estar activo.
 *  - pubPar: ERRORES que impiden publicar: parrilla sin bloques, bloques PROGRAMA sin material, con material
 *    dado de baja o no APROBADO. AVISOS (no impiden): huecos entre bloques. Al publicar: estado PUBLICADA y
 *    fecha_publicacion = ahora. La parrilla publicada es la unica fuente del orden de transmision.
 *  - Cada alta, baja y publicacion se registra en la auditoria.
 */
public class NParrilla {

    public static final String[] TIPOS_BLOQUE = {"PROGRAMA", "PAUSA_COMERCIAL"};

    private final DParrilla parrillas = new DParrilla();
    private final DBloque bloques = new DBloque();
    private final DPrograma programas = new DPrograma();
    private final DMaterial materiales = new DMaterial();
    private final NAuditoria auditoria = new NAuditoria();

    /** filtro: "*" = todas; AAAA-MM = las de ese mes. */
    public List<String[]> listar(String filtro) throws NegocioException, SQLException {
        Validador v = new Validador();
        String f = v.texto(filtro, "filtro", 10);
        v.verificar();
        if (f.equals("*")) {
            return parrillas.listar(null);
        }
        if (!f.matches("\\d{4}-(0[1-9]|1[0-2])")) {
            throw new NegocioException("El filtro debe ser <b>*</b> (todas) o un mes con formato AAAA-MM, por ejemplo 2026-11 "
                    + "(recibido: '" + Validador.esc(f) + "').");
        }
        return parrillas.listar(f);
    }

    /** Fila de la parrilla de esa fecha (ver DParrilla para las columnas). */
    public String[] mostrar(String fecha) throws NegocioException, SQLException {
        return parrillas.obtener(resolver(fecha(fecha)));
    }

    /** Bloques de la parrilla de esa fecha, ordenados por hora (ver DBloque para las columnas). */
    public List<String[]> bloques(String fecha) throws NegocioException, SQLException {
        return bloques.listarPorParrilla(resolver(fecha(fecha)));
    }

    /** insPar["fecha"]. */
    public void insertar(Usuario quien, String fechaTxt) throws NegocioException, SQLException {
        LocalDate fecha = fecha(fechaTxt);
        if (parrillas.buscarId(fecha) != null) {
            throw new NegocioException("Ya existe una parrilla para el <b>" + fecha + "</b>. Consúltela con mosPar[\"" + fecha + "\"].");
        }
        int id = parrillas.insertar(fecha, quien.getId());
        auditoria.registrar(quien, NAuditoria.INSERTAR, "parrilla", id, "Parrilla del " + fecha + " (BORRADOR)", "insPar");
    }

    /** eliPar["fecha"]. */
    public void eliminar(Usuario quien, String fechaTxt) throws NegocioException, SQLException {
        LocalDate fecha = fecha(fechaTxt);
        int id = resolver(fecha);
        exigirBorrador(id, fecha, "eliminarla");
        int spots = bloques.contarSpotsDeParrilla(id);
        if (spots > 0) {
            throw new NegocioException("No se puede eliminar la parrilla del <b>" + fecha + "</b>: tiene " + spots
                    + " spot(s) programado(s). Quítelos primero con eliSpo.");
        }
        int cantidad = bloques.listarPorParrilla(id).size();
        parrillas.eliminar(id);
        auditoria.registrar(quien, NAuditoria.ELIMINAR, "parrilla", id,
                "Parrilla del " + fecha + " con " + cantidad + " bloque(s)", "eliPar");
    }

    /** insBlo["fecha","hora_inicio","hora_fin","tipo","programa (nombre)","material (codigo)"]. */
    public void insertarBloque(Usuario quien, List<String> p) throws NegocioException, SQLException {
        Validador v = new Validador();
        LocalDate fecha = v.fecha(p.get(0), "fecha");
        LocalTime inicio = v.hora(p.get(1), "hora_inicio");
        LocalTime fin = v.hora(p.get(2), "hora_fin");
        String tipo = v.opcion(p.get(3), "tipo", TIPOS_BLOQUE);
        String programa = v.textoOpcional(p.get(4), "programa", 120);
        String material = v.textoOpcional(p.get(5), "material", 20);
        if (inicio != null && fin != null && !fin.isAfter(inicio)) {
            v.error("La <b>hora_fin</b> (" + fin + ") debe ser posterior a la <b>hora_inicio</b> (" + inicio + ").");
        }
        if ("PROGRAMA".equals(tipo) && programa == null) {
            v.error("Un bloque de tipo <b>PROGRAMA</b> necesita el nombre del programa.");
        }
        if ("PAUSA_COMERCIAL".equals(tipo) && (programa != null || material != null)) {
            v.error("Una <b>PAUSA_COMERCIAL</b> no lleva programa ni material (envíe \"\" en ambos); "
                    + "sus spots se insertan después con insSpo.");
        }
        v.verificar();

        int idParrilla = resolver(fecha);
        exigirBorrador(idParrilla, fecha, "agregarle bloques");
        String solape = bloques.buscarSolape(idParrilla, inicio, fin);
        if (solape != null) {
            v.error("El horario " + inicio + "-" + fin + " se solapa con el bloque existente " + recortar(solape) + ".");
        }
        Integer idPrograma = null;
        if (programa != null) {
            idPrograma = programas.buscarId(programa);
            if (idPrograma == null) {
                v.error("No existe el programa <b>" + Validador.esc(programa) + "</b>. Consulte los programas con lisPro[\"*\"].");
            } else if (!programas.estaActivo(idPrograma)) {
                v.error("El programa <b>" + Validador.esc(programa) + "</b> está dado de baja.");
            }
        }
        Integer idMaterial = null;
        if (material != null) {
            idMaterial = materiales.buscarId(material);
            if (idMaterial == null) {
                v.error("No existe el material <b>" + Validador.esc(material) + "</b>. Consulte los materiales con lisMat[\"*\"].");
            } else if (!materiales.estaActivo(idMaterial)) {
                v.error("El material <b>" + Validador.esc(material) + "</b> está dado de baja.");
            }
        }
        v.verificar();

        int id = bloques.insertar(idParrilla, idPrograma, idMaterial, inicio, fin, tipo);
        auditoria.registrar(quien, NAuditoria.INSERTAR, "bloque", id,
                fecha + " " + inicio + "-" + fin + " " + tipo + (programa != null ? " " + programa : ""), "insBlo");
    }

    /** eliBlo["fecha","hora_inicio"]. */
    public void eliminarBloque(Usuario quien, List<String> p) throws NegocioException, SQLException {
        Validador v = new Validador();
        LocalDate fecha = v.fecha(p.get(0), "fecha");
        LocalTime inicio = v.hora(p.get(1), "hora_inicio");
        v.verificar();

        int idParrilla = resolver(fecha);
        exigirBorrador(idParrilla, fecha, "quitarle bloques");
        Integer idBloque = bloques.buscarId(idParrilla, inicio);
        if (idBloque == null) {
            throw new NegocioException("No hay un bloque que empiece a las <b>" + inicio + "</b> en la parrilla del " + fecha
                    + ". Vea los bloques con mosPar[\"" + fecha + "\"].");
        }
        int spots = bloques.contarSpotsDeBloque(idBloque);
        if (spots > 0) {
            throw new NegocioException("No se puede quitar el bloque de las " + inicio + ": tiene " + spots
                    + " spot(s) programado(s). Quítelos primero con eliSpo.");
        }
        String[] b = bloques.obtener(idBloque);
        bloques.eliminar(idBloque);
        auditoria.registrar(quien, NAuditoria.ELIMINAR, "bloque", idBloque,
                fecha + " " + b[1] + "-" + b[2] + " " + b[3] + (b[4].isEmpty() ? "" : " " + b[4]), "eliBlo");
    }

    /**
     * pubPar["fecha"]. Revisa y publica la parrilla. Devuelve los AVISOS (no impiden publicar);
     * si hay ERRORES lanza NegocioException con todos juntos y no publica.
     */
    public List<String> publicar(Usuario quien, String fechaTxt) throws NegocioException, SQLException {
        LocalDate fecha = fecha(fechaTxt);
        int id = resolver(fecha);
        exigirBorrador(id, fecha, "publicarla de nuevo");
        List<String[]> lista = bloques.listarPorParrilla(id);

        Validador v = new Validador();
        List<String> avisos = new ArrayList<>();
        if (lista.isEmpty()) {
            v.error("La parrilla del <b>" + fecha + "</b> no tiene bloques. Agregue bloques con insBlo antes de publicar.");
        }
        LocalTime finAnterior = null;
        for (String[] b : lista) {
            LocalTime inicio = LocalTime.parse(b[1]);
            LocalTime fin = LocalTime.parse(b[2]);
            String horario = recortar(b[1]) + "-" + recortar(b[2]);
            if ("PROGRAMA".equals(b[3])) {
                if (b[5].isEmpty()) {
                    v.error("El bloque " + horario + " (" + Validador.esc(b[4]) + ") no tiene material asignado.");
                } else if ("No".equals(b[7])) {
                    v.error("El bloque " + horario + " usa el material <b>" + Validador.esc(b[5]) + "</b>, que está dado de baja.");
                } else if (!"APROBADO".equals(b[6])) {
                    v.error("El bloque " + horario + " usa el material <b>" + Validador.esc(b[5]) + "</b>, que está <b>" + b[6]
                            + "</b> (debe estar APROBADO).");
                }
            }
            if (finAnterior != null && inicio.isAfter(finAnterior)) {
                avisos.add("Hueco sin programación de " + finAnterior + " a " + inicio + ".");
            }
            finAnterior = fin;
        }
        v.verificar();

        parrillas.publicar(id);
        auditoria.registrar(quien, NAuditoria.PUBLICAR, "parrilla", id,
                "Parrilla del " + fecha + " publicada con " + lista.size() + " bloque(s) y " + avisos.size() + " aviso(s)", "pubPar");
        return avisos;
    }

    // ------------------------------------------------------------------ auxiliares

    private LocalDate fecha(String texto) throws NegocioException {
        Validador v = new Validador();
        LocalDate fecha = v.fecha(texto, "fecha");
        v.verificar();
        return fecha;
    }

    private int resolver(LocalDate fecha) throws NegocioException, SQLException {
        Integer id = parrillas.buscarId(fecha);
        if (id == null) {
            throw new NegocioException("No existe una parrilla para el <b>" + fecha + "</b>. "
                    + "Créela con insPar[\"" + fecha + "\"] o consulte las existentes con lisPar[\"*\"].");
        }
        return id;
    }

    private void exigirBorrador(int idParrilla, LocalDate fecha, String accion) throws NegocioException, SQLException {
        if (!"BORRADOR".equals(parrillas.estado(idParrilla))) {
            throw new NegocioException("La parrilla del <b>" + fecha + "</b> ya está <b>PUBLICADA</b>: no se puede " + accion + ".");
        }
    }

    /** "20:00:00-21:00:00" -> "20:00-21:00"; "20:00:00" -> "20:00". */
    private static String recortar(String horario) {
        return horario.replace(":00-", "-").replaceAll(":00$", "");
    }
}
