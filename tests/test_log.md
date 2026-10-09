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

---

## 2026-10-08 - Compilación de prueba con bcc/NASM

| # | Prueba | Resultado | Notas |
|---|---|---|---|
| 1 | Instalar bcc (Bruce's C Compiler) via apt | ❌ | Sin permisos de root |
| 2 | Clonar y compilar dev86 (bcc) desde GitHub | ⚠️ | bcc compilado pero bcc-cpp falló (errores de gcc moderno) |
| 3 | Instalar NASM | ❌ | Sin permisos de root |
| 4 | Crear .COM manualmente con Python | ✅ | hello_test.com (651 bytes, 395 bytes de código) |
| 5 | Convertir .COM a Intel HEX | ✅ | hello_test.hex (1.8 KB, 43 líneas, formato DOS correcto) |

### Próximas pruebas:
- Cargar hello_test.hex al PDT 3100 via SENDHEX
- Verificar que aparezca "Hello from Python!" en pantalla
- Si funciona: comenzar a implementar más funciones del BIOS

### Archivos generados:
- `src/hello_test.com` - Ejecutable .COM de 16-bit (651 bytes)
- `src/hello_test.hex` - Intel HEX con formato DOS (1.8 KB)
- `src/hello_test.asm` - Source en ensamblador NASM (referencia)
- `tools/exe2hex.py` - Actualizado para soportar .EXE y .COM

---

## 2026-10-08 - Prueba de carga de hello_test.hex

### Resultado: ❌ FALLO - El dispositivo borró el NVM y no arrancó nuestra app

### Qué pasó:
1. El PDT 3100 inició y mostró "ERASING NVM" ← esto BORRÓ la EEPROM
2. Después mostró "NVM Loader 1.20-00" (versión diferente al MAME ROM que era 1.02-00)
3. Mostró menú "Protocol" con opciones: Standard, 2-Way, Spectrum
4. Usuario seleccionó "Standard"
5. Pidió opciones de velocidad y comunicación
6. Mostró "Connecting to host"

### Análisis del fallo:
El problema es que nuestro hello_test.hex era un simple .COM (651 bytes) convertido a HEX.
PERO el PDT 3100 no ejecuta .COM sueltos - espera una IMAGEN COMPLETA del NVM que incluye:

1. Boot sector (formato "MSI BOOT" con BPB)
2. Tabla FAT12
3. Root directory con entradas de archivos
4. CONFIG.SYS que especifica qué programas cargar
5. Los programas .EXE reales (MAIN.EXE, SCAN3000.EXE)

El runtime.hex original (147KB) tiene TODA esta estructura. Nuestro hello_test.hex
(1.8KB) solo tenía el código binario del .COM sin estructura de filesystem.

### Información descubierta:
- NVM Loader del dispositivo: versión 1.20-00 (más nueva que la del MAME ROM: 1.02-00)
- El NVM Loader tiene menú de Protocol: Standard, 2-Way, Spectrum
- Puede descargar aplicaciones via red (Spectrum), 2-Way modem, o serial (Standard)

### Próximo paso:
1. URGENTE: Flashear runtime.hex original para recuperar el dispositivo
2. Crear imagen NVM completa con filesystem FAT12 + boot sector + CONFIG.SYS + nuestro programa

---

## 2026-10-08 - Creación de NVM Builder + imagen NVM completa

### Hallazgo CRÍTICO:
El PDT 3100 NO hace verificación CRC. El hello_test.hex se transfirió y escribió
al NVM correctamente (vimos "ERASING NVM"). El problema fue que enviamos un .COM
suelto (sin filesystem) en lugar de una imagen NVM completa.

### Solución: NVM Builder
Creado `tools/nvm_builder.py` que:
1. Toma el runtime.hex original como BASE (con filesystem FAT12 completo)
2. Reemplaza el contenido de MAIN.EXE con nuestro programa
3. Mantiene toda la estructura del filesystem intacta
4. Genera Intel HEX con formato DOS correcto

### Archivos generados:
- `tools/nvm_builder.py` - herramienta para construir imágenes NVM
- `src/hello_bare.bin` - código 8086 puro (359 bytes, sin PSP)
- `src/hello_nvm.hex` - imagen NVM completa (416 KB, mismo tamaño que original)

### Próximo paso: cargar hello_nvm.hex al PDT 3100 y probar

---

## 2026-10-09 - Prueba de hello_nvm.hex (imagen NVM con MAIN.EXE reemplazado)

### Resultado: ❌ FALLO - Mismo comportamiento que hello_test.hex

### Qué pasó:
- El dispositivo mostró "ERASING NVM"
- Luego pasó a "NVM Loader 1.20-00"
- Mismo comportamiento que antes: el NVM se borra pero la app no arranca

### Análisis:
Modificar el runtime.hex original (reemplazando MAIN.EXE) NO funciona.
El problema podría ser:
1. El BIOS SÍ verifica algo (no CRC, pero quizás checksum o tamaño)
2. La estructura del MZ EXE que generamos no es compatible
3. El shell.com (en drive A:) no puede cargar nuestro EXE
4. Hay dependencias en el overlay/librería que MAIN.EXE necesita

### NUEVO ENFOQUE: Crear imagen NVM desde cero
En lugar de modificar el runtime.hex existente, crear una imagen NVM
completamente nueva con:
- Boot sector MSI BOOT con BPB
- FAT12 filesystem creado desde cero
- CONFIG.SYS simple
- Nuestro programa como .EXE
- Sin depender del runtime.hex original
