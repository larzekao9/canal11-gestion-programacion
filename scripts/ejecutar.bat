@echo off
rem Ejecuta el sistema con un PERFIL de configuracion (obligatorio, para no tocar lo real por error).
rem   scripts\ejecutar.bat local --instalar        usa config.local.properties (base y correo locales; ver config.local.properties.example)
rem   scripts\ejecutar.bat real                    usa config.properties (base y correo del curso)
rem   scripts\ejecutar.bat real --probar "help" larzekaobnc@gmail.com
rem Compilar es igual para los dos: scripts\compilar.bat
cd /d "%~dp0.."
if "%1"=="local" (set CONFIG=config.local.properties) else if "%1"=="real" (set CONFIG=config.properties) else (
    echo Uso: scripts\ejecutar.bat local^|real [opciones]
    exit /b 1
)
shift
if not exist %CONFIG% (
    if "%CONFIG%"=="config.local.properties" (copy config.local.properties.example %CONFIG% >nul) else (echo Falta %CONFIG% & exit /b 1)
)
java -Dcanal11.config=%CONFIG% -cp "out;lib\postgresql-42.7.4.jar" canal11.App %1 %2 %3 %4 %5 %6 %7 %8 %9
