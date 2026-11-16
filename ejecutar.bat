@echo off
rem Ejecuta el sistema. Sin parametros: revisa el buzon y responde.
rem   ejecutar.bat --instalar
rem   ejecutar.bat --probar "help" larzekaobnc@gmail.com
rem   ejecutar.bat --buzon
rem   ejecutar.bat --enviar-prueba correo@destino.com
cd /d "%~dp0"
java -cp "out;lib\postgresql-42.7.4.jar" canal11.App %*
