package canal11.negocio;

/** Actores del sistema aprobados en el CU1. */
public enum Rol {
    ADMINISTRADOR("Administrador"),
    PROGRAMADOR("Programador"),
    ENCARGADO("Encargado de Contenidos");

    private final String nombre;

    Rol(String nombre) {
        this.nombre = nombre;
    }

    public String getNombre() {
        return nombre;
    }

    /** Convierte el texto de la BD o de un parametro ("programador") en Rol; null si no existe. */
    public static Rol desde(String texto) {
        for (Rol r : values()) {
            if (r.name().equalsIgnoreCase(texto == null ? "" : texto.trim())) {
                return r;
            }
        }
        return null;
    }
}
