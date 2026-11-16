package canal11.comunicacion;

import canal11.config.Registro;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/**
 * Hilo que revisa el buzon cada N segundos (ciclo "forever" del servidor).
 * En cada vuelta: conecta por POP3, descarga las cabeceras de todos los correos, los marca para borrar,
 * cierra con QUIT (ahi se borran) y avisa al OyenteCorreo con la lista. El oyente decide que responder.
 *
 * Si falla la conexion (servidor caido, sin internet) solo se informa y se reintenta en la siguiente vuelta:
 * el hilo nunca se detiene por un error.
 */
public class HiloCorreo implements Runnable {

    private final String host;
    private final int puerto;
    private final String usuario;
    private final String password;
    private final int intervaloSegundos;
    private final OyenteCorreo oyente;
    private volatile boolean activo = true;

    public HiloCorreo(String host, int puerto, String usuario, String password, int intervaloSegundos, OyenteCorreo oyente) {
        this.host = host;
        this.puerto = puerto;
        this.usuario = usuario;
        this.password = password;
        this.intervaloSegundos = intervaloSegundos;
        this.oyente = oyente;
    }

    @Override
    public void run() {
        while (activo) {
            try {
                List<Correo> correos = descargar();
                if (!correos.isEmpty()) {
                    oyente.alRecibirCorreos(correos);
                }
            } catch (IOException e) {
                System.err.println("[HiloCorreo] No se pudo revisar el buzon (" + host + ":" + puerto + "): " + e.getMessage());
                Registro.errorSistema("POP3 - no se pudo revisar el buzon (" + host + ":" + puerto + ")", e);
            } catch (RuntimeException e) {
                System.err.println("[HiloCorreo] Error inesperado: " + e);
                Registro.errorSistema("HiloCorreo - error inesperado", e);
            }
            try {
                Thread.sleep(intervaloSegundos * 1000L);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                activo = false;
            }
        }
    }

    /** Detiene el hilo al terminar la vuelta actual. */
    public void detener() {
        activo = false;
    }

    /** Descarga todos los correos del buzon y los borra (el QUIT al cerrar aplica los DELE). */
    private List<Correo> descargar() throws IOException {
        List<Correo> correos = new ArrayList<>();
        try (ClientePOP3 pop = new ClientePOP3(host, puerto)) {
            pop.login(usuario, password);
            int total = pop.cantidadMensajes();
            for (int i = 1; i <= total; i++) {
                correos.add(pop.obtener(i));
                pop.eliminar(i);
            }
        }
        return correos;
    }
}
