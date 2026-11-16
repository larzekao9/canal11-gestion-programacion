package canal11.datos;

import canal11.config.Config;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.sql.Statement;

/**
 * Crea el esquema y ejecuta los scripts de la carpeta sql/ (tablas y datos iniciales).
 * Uso: ejecutar.bat --instalar
 */
public final class Instalador {

    private static final String[] SCRIPTS = {"sql/01_tablas.sql", "sql/02_datos.sql"};

    private Instalador() {
    }

    public static void instalar() throws IOException, SQLException {
        String esquema = Config.get("db.esquema");
        if (!esquema.matches("[a-z_][a-z0-9_]*")) {
            throw new IllegalArgumentException("Nombre de esquema invalido: " + esquema);
        }
        String urlBase = "jdbc:postgresql://" + Config.get("db.host") + ":" + Config.get("db.puerto") + "/" + Config.get("db.nombre");
        try (Connection c = DriverManager.getConnection(urlBase, Config.get("db.usuario"), Config.get("db.password"));
             Statement st = c.createStatement()) {
            st.execute("CREATE SCHEMA IF NOT EXISTS " + esquema);
            st.execute("SET search_path TO " + esquema);
            for (String script : SCRIPTS) {
                int n = 0;
                for (String sentencia : leerSentencias(Path.of(script))) {
                    st.execute(sentencia);
                    n++;
                }
                System.out.println("  " + script + ": " + n + " sentencia(s) ejecutadas");
            }
        }
        System.out.println("Esquema '" + esquema + "' listo en " + Config.get("db.nombre") + ".");
    }

    /** Separa el script en sentencias por ';' al final de linea, ignorando comentarios "--". */
    private static java.util.List<String> leerSentencias(Path archivo) throws IOException {
        java.util.List<String> sentencias = new java.util.ArrayList<>();
        StringBuilder actual = new StringBuilder();
        for (String linea : Files.readAllLines(archivo, StandardCharsets.UTF_8)) {
            String l = linea.strip();
            if (l.isEmpty() || l.startsWith("--")) {
                continue;
            }
            actual.append(linea).append('\n');
            if (l.endsWith(";")) {
                sentencias.add(actual.toString().strip());
                actual.setLength(0);
            }
        }
        if (!actual.toString().isBlank()) {
            sentencias.add(actual.toString().strip());
        }
        return sentencias;
    }
}
