package canal11.config;

import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Properties;

/**
 * Lee la configuracion desde config.properties (carpeta desde donde se ejecuta el programa).
 * Si una clave no esta en el archivo se usa el valor por defecto definido aqui.
 */
public final class Config {

    private static final Properties PROPS = new Properties();

    static {
        // Servidor de correo del curso
        PROPS.setProperty("mail.usuario", "grupo12sa");
        PROPS.setProperty("mail.password", "");
        PROPS.setProperty("mail.direccion", "grupo12sa@tecnoweb.org.bo");
        PROPS.setProperty("pop3.host", "mail.tecnoweb.org.bo");
        PROPS.setProperty("pop3.puerto", "110");
        PROPS.setProperty("smtp.host", "mail.tecnoweb.org.bo");
        PROPS.setProperty("smtp.puerto", "25");
        // Base de datos del curso
        PROPS.setProperty("db.host", "db.tecnoweb.org.bo");
        PROPS.setProperty("db.puerto", "5432");
        PROPS.setProperty("db.nombre", "db_grupo12sa");
        PROPS.setProperty("db.usuario", "grupo12sa");
        PROPS.setProperty("db.password", "");
        PROPS.setProperty("db.esquema", "canal11");
        // Cada cuantos segundos se revisa el buzon
        PROPS.setProperty("app.intervalo", "10");

        try (InputStreamReader in = new InputStreamReader(
                new FileInputStream("config.properties"), StandardCharsets.UTF_8)) {
            PROPS.load(in);
        } catch (IOException e) {
            System.out.println("[Config] No se encontro config.properties; se usan valores por defecto.");
        }
    }

    private Config() {
    }

    public static String get(String clave) {
        String v = PROPS.getProperty(clave);
        return v == null ? "" : v.trim();
    }

    public static int getInt(String clave) {
        return Integer.parseInt(get(clave));
    }
}
