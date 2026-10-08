# Log de Pruebas - PDT 3100 Development System

## Historial de pruebas

| Fecha | Prueba | Resultado | Notas |
|---|---|---|---|
| 2026-10-08 | Análisis del runtime.hex original (147KB) | ✅ | Arquitectura: 80186 + FAT filesystem + MAIN.EXE + overlay |
| 2026-10-08 | Localización del flag de modo DS:0x1091 | ✅ | Variable global con 6 referencias (1 escritura + 5 lecturas) |
| 2026-10-08 | Diseño de parches para forzar modo Admin | ✅ | 6 parches (A-F), 138 bytes total |
| 2026-10-08 | Generación de runtime_patched.hex | ✅ | Formato Intel HEX con CRLF + Ctrl-Z + estructura de segmentos idéntica |
| 2026-10-08 | Flash de runtime_patched.hex al PDT 3100 | ⚠️ | Status 0000 (transfer OK) pero boot falla - BIOS rechaza por CRC |
| 2026-10-08 | Recuperación con runtime.hex original | ✅ | Dispositivo funcionando nuevamente en modo RunTime |
| 2026-10-08 | Análisis del MAME ROM (3 chips de 128KB) | ✅ | U8=DR-DOS+BIOS, U9=NVM Loader 1.02-00, U11=EEPROM vacía |
| 2026-10-08 | Búsqueda de tabla CRC en MAME ROM | ✅ | Tabla CRC16-CCITT encontrada en U8 @ 0x19D13 (poly 0x1021) |
| 2026-10-08 | Búsqueda del CRC esperado en runtime.hex | ❌ | No encontrado - el CRC está hardcodeado en el código del BIOS |
| 2026-10-08 | Búsqueda del ADK oficial de Symbol | ❌ | No disponible públicamente. Solo documentación (YUMPU) |
| 2026-10-08 | Búsqueda de MSVC 1.52c | ✅ | Disponible en archive.org (ISO image, 195MB) |
| 2026-10-08 | Creación del proyecto pdt3100-dev-system | ✅ | Repo creado en GitHub con estructura inicial |

## Próximas pruebas planeadas

| # | Prueba | Estado |
|---|---|---|
| 1 | Descargar e instalar MSVC 1.52c en DOSBox | Pendiente |
| 2 | Compilar hello.c con MSVC 1.52c | Pendiente |
| 3 | Convertir hello.exe a hello.hex con exe2hex.py | Pendiente |
| 4 | Cargar hello.hex al PDT 3100 via SENDHEX | Pendiente |
| 5 | Verificar "Hello World" en pantalla del PDT 3100 | Pendiente |
| 6 | Documentar funciones del BIOS desde MAME ROM | Pendiente |
| 7 | Implementar librería libbios (wrapper de INT calls) | Pendiente |
| 8 | Crear programa de ejemplo con scanner láser | Pendiente |
