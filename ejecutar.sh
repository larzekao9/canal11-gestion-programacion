#!/bin/bash
# Ejecuta el sistema. Sin parametros: revisa el buzon y responde.
cd "$(dirname "$0")" || exit 1
java -cp "out:lib/postgresql-42.7.4.jar" canal11.App "$@"
