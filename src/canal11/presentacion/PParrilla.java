package canal11.presentacion;

import canal11.negocio.NParrilla;
import canal11.negocio.Usuario;

import java.util.ArrayList;
import java.util.List;

/**
 * CU3 - Capa de presentacion de la parrilla: lee los parametros, llama a NParrilla y arma el HTML.
 * Sin SQL ni reglas de negocio. Cada respuesta trae los comandos siguientes ya rellenados.
 */
public class PParrilla {

    /** Columnas de la ficha de la parrilla (mismo orden que DParrilla). */
    private static final String[] COLUMNAS = {"ID", "Fecha", "Estado", "Creada por", "Fecha de creación", "Fecha de publicación", "Bloques"};

    private final NParrilla negocio = new NParrilla();

    /** lisPar["*"] | lisPar["2026-11"] */
    public Respuesta listar(Usuario u, List<String> p) throws Exception {
        List<String[]> filas = negocio.listar(p.get(0));
        List<String[]> tabla = new ArrayList<>();
        for (String[] f : filas) {
            tabla.add(new String[]{
                    Html.esc(f[1]),
                    Html.esc(f[2]),
                    Html.esc(f[6]),
                    Html.esc(f[3]),
                    Html.esc(f[5]),
                    Html.codigo("mosPar[\"" + f[1] + "\"]")});
        }
        String filtro = p.get(0).trim().equals("*") ? "Todas las parrillas." : "Parrillas del mes " + p.get(0).trim() + ".";
        return new Respuesta("Parrillas", Html.parrafo(Html.esc(filtro))
                + Html.tablaHtml(new String[]{"Fecha", "Estado", "Bloques", "Creada por", "Publicada", "Ver parrilla"}, tabla)
                + Html.total(filas.size()));
    }

    /** mosPar["fecha"] */
    public Respuesta mostrar(Usuario u, List<String> p) throws Exception {
        String[] f = negocio.mostrar(p.get(0));
        return new Respuesta("Parrilla del " + f[1], vista(f, p.get(0)));
    }

    /** insPar["fecha"] */
    public Respuesta insertar(Usuario u, List<String> p) throws Exception {
        negocio.insertar(u, p.get(0));
        String[] f = negocio.mostrar(p.get(0));
        return new Respuesta("Parrilla creada",
                Html.exito("La parrilla del <b>" + f[1] + "</b> fue creada en <b>BORRADOR</b>. Agregue sus bloques con insBlo.")
                        + vista(f, p.get(0)));
    }

    /** eliPar["fecha"] */
    public Respuesta eliminar(Usuario u, List<String> p) throws Exception {
        String[] f = negocio.mostrar(p.get(0));
        negocio.eliminar(u, p.get(0));
        return new Respuesta("Parrilla eliminada",
                Html.exito("La parrilla del <b>" + f[1] + "</b> y sus " + f[6] + " bloque(s) fueron eliminados.")
                        + Html.parrafo("Crear de nuevo: " + Html.codigo("insPar[\"" + f[1] + "\"]")));
    }

    /** insBlo["fecha","hora_inicio","hora_fin","tipo","programa","material"] */
    public Respuesta insertarBloque(Usuario u, List<String> p) throws Exception {
        negocio.insertarBloque(u, p);
        String[] f = negocio.mostrar(p.get(0));
        return new Respuesta("Bloque agregado",
                Html.exito("El bloque fue agregado a la parrilla del <b>" + f[1] + "</b>.") + vista(f, p.get(0)));
    }

    /** eliBlo["fecha","hora_inicio"] */
    public Respuesta eliminarBloque(Usuario u, List<String> p) throws Exception {
        negocio.eliminarBloque(u, p);
        String[] f = negocio.mostrar(p.get(0));
        return new Respuesta("Bloque quitado",
                Html.exito("El bloque de las <b>" + Html.esc(p.get(1).trim()) + "</b> fue quitado de la parrilla.") + vista(f, p.get(0)));
    }

    /** pubPar["fecha"] */
    public Respuesta publicar(Usuario u, List<String> p) throws Exception {
        List<String> avisos = negocio.publicar(u, p.get(0));
        String[] f = negocio.mostrar(p.get(0));
        String html = Html.exito("La parrilla del <b>" + f[1] + "</b> fue <b>PUBLICADA</b>. "
                + "Es ahora la única fuente del orden de transmisión.");
        if (!avisos.isEmpty()) {
            html += Html.info("<b>Avisos</b> (no impidieron publicar):" + Html.lista(escapar(avisos)));
        }
        return new Respuesta("Parrilla publicada", html + vista(f, p.get(0)));
    }

    // ------------------------------------------------------------------ vista comun

    /** Ficha de la parrilla + tabla de bloques + acciones sugeridas. */
    private String vista(String[] f, String fechaTxt) throws Exception {
        List<String[]> bloques = negocio.bloques(fechaTxt);
        boolean borrador = "BORRADOR".equals(f[2]);
        String fecha = f[1];

        List<String[]> tabla = new ArrayList<>();
        for (String[] b : bloques) {
            String material = b[5].isEmpty() ? ("PROGRAMA".equals(b[3]) ? "SIN MATERIAL" : "") : b[5];
            String estado = b[5].isEmpty() ? "" : ("No".equals(b[7]) ? b[6] + " (material de baja)" : b[6]);
            tabla.add(new String[]{
                    Html.esc(hora(b[1]) + " - " + hora(b[2])),
                    Html.esc(b[3]),
                    Html.esc(b[4]),
                    Html.esc(material),
                    Html.esc(estado),
                    borrador ? Html.codigo("eliBlo[\"" + fecha + "\",\"" + hora(b[1]) + "\"]") : ""});
        }
        String[] cabecera = borrador
                ? new String[]{"Horario", "Tipo", "Programa", "Material", "Estado del material", "Quitar"}
                : new String[]{"Horario", "Tipo", "Programa", "Material", "Estado del material", ""};

        StringBuilder sb = new StringBuilder(Html.ficha(COLUMNAS, f));
        sb.append(Html.subtitulo("Bloques"));
        sb.append(Html.tablaHtml(cabecera, tabla));
        if (borrador) {
            String siguiente = bloques.isEmpty() ? "20:00" : hora(bloques.get(bloques.size() - 1)[2]);
            sb.append(Html.subtitulo("Acciones (copie, cambie lo necesario y envíe)"));
            sb.append(Html.parrafo("Agregar bloque de programa: "
                    + Html.codigo("insBlo[\"" + fecha + "\",\"" + siguiente + "\",\"HH:MM\",\"PROGRAMA\",\"nombre del programa\",\"CODIGO\"]")));
            sb.append(Html.parrafo("Agregar pausa comercial: "
                    + Html.codigo("insBlo[\"" + fecha + "\",\"" + siguiente + "\",\"HH:MM\",\"PAUSA_COMERCIAL\",\"\",\"\"]")));
            sb.append(Html.parrafo("Revisar y publicar: " + Html.codigo("pubPar[\"" + fecha + "\"]")));
            sb.append(Html.parrafo("Eliminar la parrilla: " + Html.codigo("eliPar[\"" + fecha + "\"]")));
        } else {
            sb.append(Html.subtitulo("Siguientes pasos"));
            sb.append(Html.parrafo("Estado de emisión: " + Html.codigo("estPar[\"" + fecha + "\"]")));
        }
        return sb.toString();
    }

    /** "20:00:00" -> "20:00"; "20:00:30" se deja igual. */
    private static String hora(String h) {
        return h.endsWith(":00") && h.length() == 8 ? h.substring(0, 5) : h;
    }

    private static List<String> escapar(List<String> textos) {
        List<String> r = new ArrayList<>();
        for (String t : textos) {
            r.add(Html.esc(t));
        }
        return r;
    }
}
